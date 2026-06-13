import os
import asyncio
import json
import time
import random
from google import genai
from google.genai import types

gemini_semaphore = asyncio.Semaphore(2)

def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise Exception("GEMINI_API_KEY environment variable is not set.")
    return genai.Client(api_key=api_key)

async def upload_and_wait(file_path: str, display_name: str, yield_callback=None):
    """Upload file to Gemini Files API with exponential backoff polling."""
    client = get_client()
    start = time.perf_counter()

    if yield_callback:
        await yield_callback("Uploading preview to Gemini...")

    loop = asyncio.get_event_loop()

    # Upload file
    def _upload():
        return client.files.upload(file=file_path, config={'display_name': display_name})

    uploaded_file = await loop.run_in_executor(None, _upload)
    upload_elapsed = time.perf_counter() - start
    print(f"[PERF] Gemini upload: {upload_elapsed:.1f}s")

    if yield_callback:
        await yield_callback("Preview uploaded. Waiting for Gemini processing...")

    # Exponential backoff polling: 2s, 4s, 8s, 10s, 10s, ...
    poll_start = time.perf_counter()
    delay = 2.0
    max_delay = 10.0
    poll_count = 0

    while True:
        def _get_file():
            return client.files.get(name=uploaded_file.name)

        file_info = await loop.run_in_executor(None, _get_file)
        poll_count += 1

        if file_info.state == "ACTIVE":
            break
        elif file_info.state == "FAILED":
            raise Exception("Gemini failed to process the video.")

        await asyncio.sleep(delay)
        delay = min(delay * 1.5, max_delay)  # exponential backoff capped at 10s

    poll_elapsed = time.perf_counter() - poll_start
    total_elapsed = time.perf_counter() - start
    print(f"[PERF] Gemini poll: {poll_elapsed:.1f}s ({poll_count} polls)  |  Total upload+wait: {total_elapsed:.1f}s")

    if yield_callback:
        await yield_callback("Video processing complete. Analyzing moments...")

    return file_info

async def analyze_and_generate(file_uris: list[str], property_name: str, duration: str, style: str, yield_callback=None) -> dict:
    """Single Gemini call: analyze multiple videos and build one 20-30s reel."""
    client = get_client()

    prompt = f"""Property: '{property_name}'
Goal: Build ONE {style} style vertical reel targeting exactly {duration} duration.
You have been provided {len(file_uris)} video clips (indices 0 to {len(file_uris)-1}).

TASKS:
1. Detect Property Type (apartment, house, villa, penthouse).
2. Classify every clip (e.g. exterior, entrance, living_room, kitchen, bedroom, pool, drone_view, etc) and score its quality (0-100). Reject blurry, bad lighting, or duplicate footage.
3. Select ONLY the strongest 8-12 clips.
4. Smart Reel Ordering:
   - If House/Villa: Exterior -> Entrance -> Living Room -> Dining -> Kitchen -> Bedroom -> Bathroom -> Balcony -> Backyard -> Pool -> Closing.
   - If Apartment/Penthouse: Building Exterior -> Entrance -> Living Room -> Dining -> Kitchen -> Bedroom -> Bathroom -> Balcony -> Amenities -> View -> Closing.
   NEVER use upload order. Always sequence based on the property type logic above.
5. Provide a highly engaging social media hook, a 4-5 line description of the property, and hashtags.

Return strict JSON:
- 'property_type': string
- 'title': string
- 'hook': string
- 'description': string (4-5 lines of text)
- 'hashtags': array of strings
- 'selected_clips': array of objects {{'video_index': int, 'scene_type': str, 'score': int, 'reason': str, 'start': 'MM:SS', 'end': 'MM:SS'}}
- 'final_order': array of integers (these MUST match the 'video_index' values from selected_clips, defining the exact storyline sequence)."""

    schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "property_type": types.Schema(type=types.Type.STRING),
            "title": types.Schema(type=types.Type.STRING),
            "hook": types.Schema(type=types.Type.STRING),
            "description": types.Schema(type=types.Type.STRING),
            "hashtags": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
            "selected_clips": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "video_index": types.Schema(type=types.Type.INTEGER),
                        "scene_type": types.Schema(type=types.Type.STRING),
                        "score": types.Schema(type=types.Type.INTEGER),
                        "reason": types.Schema(type=types.Type.STRING),
                        "start": types.Schema(type=types.Type.STRING),
                        "end": types.Schema(type=types.Type.STRING),
                    },
                    required=["video_index", "scene_type", "score", "reason", "start", "end"]
                )
            ),
            "final_order": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.INTEGER))
        },
        required=["property_type", "title", "hook", "description", "hashtags", "selected_clips", "final_order"]
    )

    loop = asyncio.get_event_loop()
    max_retries = 5
    backoff_schedule = [5, 10, 20, 40, 60]

    async with gemini_semaphore:
        for attempt in range(max_retries + 1):
            # Fallback model strategy: Pro for first 3 attempts, Flash for the rest
            model_name = 'gemini-2.5-pro' if attempt < 3 else 'gemini-2.5-flash'
            start_attempt = time.perf_counter()

            try:
                def _generate():
                    contents = [types.Part.from_uri(file_uri=uri, mime_type="video/mp4") for uri in file_uris]
                    contents.append(prompt)
                    
                    return client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=schema,
                            temperature=0.5,
                        ),
                    )

                # Timeout Protection
                future = loop.run_in_executor(None, _generate)
                response = await asyncio.wait_for(future, timeout=90.0)

                elapsed = time.perf_counter() - start_attempt
                print(f"[PERF] Gemini {model_name} success on attempt {attempt+1}: {elapsed:.1f}s")

                try:
                    return json.loads(response.text)
                except json.JSONDecodeError:
                    raise Exception(f"Failed to decode Gemini response as JSON: {response.text}")

            except Exception as e:
                error_str = str(e)
                is_timeout = isinstance(e, asyncio.TimeoutError)
                is_retryable = is_timeout or any(code in error_str for code in ["429", "500", "502", "503", "504", "UNAVAILABLE", "Model overloaded"])
                
                elapsed = time.perf_counter() - start_attempt

                if attempt == max_retries or not is_retryable:
                    if attempt == max_retries:
                        print(f"[ERROR] Gemini exhausted all {max_retries} retries. Final error: {error_str}")
                        raise Exception("Gemini service temporarily unavailable after multiple retries.")
                    else:
                        print(f"[ERROR] Non-retryable Gemini error: {error_str}")
                        raise

                base_delay = backoff_schedule[attempt]
                jitter = random.uniform(0, 3)
                delay = base_delay + jitter

                print(f"[RETRY] Attempt {attempt+1} failed ({elapsed:.1f}s). Model: {model_name}. Code: {error_str[:60]}... Delaying {delay:.1f}s")

                if yield_callback:
                    await yield_callback(f"AI servers busy, retrying... (Retry {attempt+1} of 5)")

                await asyncio.sleep(delay)

async def generate_variations(property_name: str, timeline: list) -> dict:
    """Phase 2: Generate 3 distinct text variations (Luxury, Viral, Realtor) based on the timeline."""
    client = get_client()

    # Summarize timeline for context
    scenes = [f"Index {c.get('video_index', i)}: {c.get('scene_type', 'scene')} ({c.get('start', '0')}-{c.get('end', '5')}s) - {c.get('reason', '')}" for i, c in enumerate(timeline)]
    timeline_context = "\n".join(scenes)

    prompt = f"""Property: '{property_name}'
Goal: Generate 3 distinct Reel Variations (Luxury, Instagram Viral, Realtor Style) using the provided Pool of Scenes.
For each variation:
1. Write a hook, description, and hashtags that match the style.
2. Create a custom sequence of video clips by selecting and ordering from the pool of scenes. You can reuse clips, drop clips, or completely change the order to fit the vibe!
   - Luxury: Slower paced, focus on beautiful wide shots, pools, and main rooms.
   - Instagram Viral: Fast-paced, start with the most dramatic/unique shot as the hook, quick cuts.
   - Realtor Style: Traditional logical walkthrough (Exterior -> Entrance -> Living -> Kitchen).

Pool of Scenes:
{timeline_context}

Return strict JSON:
- 'variations': array of exactly 3 objects.
  Each object MUST have:
  - 'style': string (either 'Luxury', 'Instagram Viral', or 'Realtor Style')
  - 'hook': string
  - 'description': string
  - 'hashtags': array of strings
  - 'custom_sequence': array of integers (referencing the 'Index' values from the pool to define the exact sequence of this cut)"""

    schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "variations": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "style": types.Schema(type=types.Type.STRING),
                        "hook": types.Schema(type=types.Type.STRING),
                        "description": types.Schema(type=types.Type.STRING),
                        "hashtags": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
                        "custom_sequence": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.INTEGER)),
                    },
                    required=["style", "hook", "description", "hashtags", "custom_sequence"]
                )
            )
        },
        required=["variations"]
    )

    loop = asyncio.get_event_loop()
    
    def _generate():
        return client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0.5,
            )
        )

    await gemini_semaphore.acquire()
    try:
        response = await loop.run_in_executor(None, _generate)
        text = response.text
        if text.startswith("```json"):
            text = text[7:-3]
        return json.loads(text)
    except Exception as e:
        print(f"[ERROR] Gemini variations generation failed: {e}")
        raise
    finally:
        gemini_semaphore.release()
