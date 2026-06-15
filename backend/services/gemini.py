import os
import asyncio
import json
import time
import random
from google import genai
from google.genai import types

gemini_semaphore = asyncio.Semaphore(2)

# ── Property Tour Scene Order ──────────────────────────────
SCENE_ORDER = [
    "drone", "aerial", "exterior", "entrance", "lobby",
    "living room", "kitchen", "dining", "bedroom", "bathroom",
    "balcony", "pool", "gym", "parking", "garden",
    "amenities", "closing drone", "closing"
]

# ── Global Client Singleton ──────────────────────────────────
_gemini_client = None

def get_client():
    global _gemini_client
    if _gemini_client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY environment variable is not set.")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client

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

    # Exponential backoff polling: 2s, 3s, 4.5s, 6.75s, 10s, 10s, ...
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
        delay = min(delay * 1.5, max_delay)

    poll_elapsed = time.perf_counter() - poll_start
    total_elapsed = time.perf_counter() - start
    print(f"[PERF] Gemini poll: {poll_elapsed:.1f}s ({poll_count} polls)  |  Total upload+wait: {total_elapsed:.1f}s")

    if yield_callback:
        await yield_callback("Video processing complete. Analyzing moments...")

    return file_info


def _calculate_dynamic_duration(clip_count: int, target_duration: str) -> str:
    """Calculate dynamic reel duration based on clip count and target platform mode.
    '30 sec' or '45 sec' implies SHORTS MODE.
    '1 min' or '2 min' implies YOUTUBE MODE.
    """
    is_youtube = 'min' in target_duration.lower()
    
    if not is_youtube:
        # SHORTS MODE
        if clip_count <= 10:
            return "30-45 seconds"
        elif clip_count <= 20:
            return "45-60 seconds"
        else:
            return "60 seconds maximum"
    else:
        # YOUTUBE MODE
        if clip_count <= 10:
            return "60-90 seconds"
        elif clip_count <= 20:
            return "90-120 seconds"
        else:
            return "120 seconds maximum"


async def analyze_and_generate(file_uris: list[str], property_name: str, duration: str, style: str, duplicate_sensitivity: str = "Low", yield_callback=None) -> dict:
    """Coverage-First AI Selection Engine."""
    client = get_client()
    clip_count = len(file_uris)
    dynamic_duration = _calculate_dynamic_duration(clip_count, duration)

    prompt = f"""Property: '{property_name}'
Total Uploaded Clips: {clip_count} (indices 0 to {clip_count - 1})

═══ YOUR #1 PRIORITY: MAXIMIZE FOOTAGE COVERAGE ═══

You are a professional real estate video editor. Your job is to create a COMPLETE property tour that uses NEARLY ALL uploaded footage.

COVERAGE TARGET: Use 80-95% of all clips. Use at least one segment from every unique uploaded clip whenever possible.
If {clip_count} clips are uploaded, you should select at least {max(1, int(clip_count * 0.85))} clips.

═══ DUPLICATE REMOVAL RULES (VERY STRICT) ═══

ONLY remove a clip if ALL of the following are true:
1. It shows the EXACT same scene as another clip
2. It has the EXACT same camera angle (within 10 degrees)  
3. Visual similarity is above 95%

Duplicate Sensitivity Setting: {duplicate_sensitivity}

═══ OPENING SHOT SELECTION ═══

Choose the strongest opening shot from: Drone, Exterior, or Best Luxury Scene.
AVOID using Parking, Bathroom, or Storage Area as the opening shot under any circumstances (unless no other clips exist).

═══ PROPERTY TOUR STORY ENGINE ═══

Do NOT use the raw upload order. Do NOT use score-only ordering.
Detect scene categories and automatically build a logical property walkthrough.

Preferred sequence:
1. OPENING: Drone, Exterior, Entrance
2. MAIN TOUR: Lobby, Living Room, Dining, Kitchen
3. PRIVATE AREAS: Bedroom, Bathroom, Balcony
4. AMENITIES: Pool, Gym, Garden, Clubhouse
5. FINAL SECTION: Parking, Exterior, Closing Drone

Parking should NEVER be used as the opening shot. Place it near the end.

═══ SCENE DIVERSITY ═══

Never place more than 2 clips of the same scene_type consecutively.

═══ DYNAMIC CLIP DURATION ═══

Extract 3-5 seconds from the high-quality portions of each clip.
- Quality score 90-100: 4-5 seconds
- Quality score below 90: 3-4 seconds

Target total reel duration: {dynamic_duration} (scales intelligently based on {clip_count} unique clips and the requested format).

═══ STORYBOARD VALIDATION ═══

Before outputting, verify:
- Does the reel start with a premium opening shot?
- Does it follow the logical property tour?
- Are all major categories represented?
- Is parking placed near the end?
- Is there a strong closing shot?

═══ SCORING (per clip) ═══

Score each clip 0-100 on: visual_quality_score, lighting_score, stability_score, luxury_appeal, engagement_score.
Assign confidence_score (0-100).

═══ OUTPUT FORMAT ═══

Return strict JSON with these fields:
- property_type, title, hook, description, hashtags
- total_analyzed_duration_sec, total_selected_duration_sec
- duplicates_removed_count
- coverage_analytics: {{ uploaded_count, duplicates_removed, selected_count, coverage_percentage }}
- removed_clips: array of {{ video_index, reason }}
- selected_clips: array of {{ video_index, scene_type, confidence_score, visual_quality_score, lighting_score, stability_score, luxury_appeal, engagement_score, clip_duration_sec, reason, start, end }}
- final_order: array of video_index integers defining the exact storyline sequence"""

    schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "property_type": types.Schema(type=types.Type.STRING),
            "title": types.Schema(type=types.Type.STRING),
            "hook": types.Schema(type=types.Type.STRING),
            "description": types.Schema(type=types.Type.STRING),
            "hashtags": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
            "total_analyzed_duration_sec": types.Schema(type=types.Type.INTEGER),
            "total_selected_duration_sec": types.Schema(type=types.Type.INTEGER),
            "duplicates_removed_count": types.Schema(type=types.Type.INTEGER),
            "coverage_analytics": types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "uploaded_count": types.Schema(type=types.Type.INTEGER),
                    "duplicates_removed": types.Schema(type=types.Type.INTEGER),
                    "selected_count": types.Schema(type=types.Type.INTEGER),
                    "coverage_percentage": types.Schema(type=types.Type.NUMBER),
                },
                required=["uploaded_count", "duplicates_removed", "selected_count", "coverage_percentage"]
            ),
            "removed_clips": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "video_index": types.Schema(type=types.Type.INTEGER),
                        "reason": types.Schema(type=types.Type.STRING)
                    },
                    required=["video_index", "reason"]
                )
            ),
            "selected_clips": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "video_index": types.Schema(type=types.Type.INTEGER),
                        "scene_type": types.Schema(type=types.Type.STRING),
                        "confidence_score": types.Schema(type=types.Type.NUMBER),
                        "visual_quality_score": types.Schema(type=types.Type.INTEGER),
                        "lighting_score": types.Schema(type=types.Type.INTEGER),
                        "stability_score": types.Schema(type=types.Type.INTEGER),
                        "luxury_appeal": types.Schema(type=types.Type.INTEGER),
                        "engagement_score": types.Schema(type=types.Type.INTEGER),
                        "clip_duration_sec": types.Schema(type=types.Type.NUMBER),
                        "reason": types.Schema(type=types.Type.STRING),
                        "start": types.Schema(type=types.Type.STRING),
                        "end": types.Schema(type=types.Type.STRING),
                    },
                    required=["video_index", "scene_type", "confidence_score", "visual_quality_score", "lighting_score", "stability_score", "luxury_appeal", "engagement_score", "clip_duration_sec", "reason", "start", "end"]
                )
            ),
            "final_order": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.INTEGER))
        },
        required=["property_type", "title", "hook", "description", "hashtags", "total_analyzed_duration_sec", "total_selected_duration_sec", "duplicates_removed_count", "coverage_analytics", "removed_clips", "selected_clips", "final_order"]
    )

    loop = asyncio.get_event_loop()
    max_retries = 5
    backoff_schedule = [5, 10, 20, 40, 60]

    async with gemini_semaphore:
        for attempt in range(max_retries + 1):
            model_name = 'gemini-2.5-flash'
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

                future = loop.run_in_executor(None, _generate)
                response = await asyncio.wait_for(future, timeout=120.0)

                elapsed = time.perf_counter() - start_attempt
                print(f"[PERF] Gemini {model_name} success on attempt {attempt+1}: {elapsed:.1f}s")

                try:
                    result = json.loads(response.text)
                except json.JSONDecodeError:
                    raise Exception(f"Failed to decode Gemini response as JSON: {response.text}")

                # ── Post-Processing: Validate Coverage ──
                selected_count = len(result.get("selected_clips", []))
                removed_count = len(result.get("removed_clips", []))
                coverage_pct = (selected_count / clip_count * 100) if clip_count > 0 else 0

                # Ensure coverage_analytics is accurate
                result["coverage_analytics"] = {
                    "uploaded_count": clip_count,
                    "duplicates_removed": removed_count,
                    "selected_count": selected_count,
                    "coverage_percentage": round(coverage_pct, 1)
                }
                result["duplicates_removed_count"] = removed_count

                print(f"[COVERAGE] {clip_count} uploaded → {removed_count} removed → {selected_count} selected → {coverage_pct:.1f}%")

                # Warn if coverage is too low
                if coverage_pct < 70 and clip_count > 3:
                    print(f"[WARNING] Coverage is only {coverage_pct:.1f}%. Expected 80-95%. Gemini may have been too aggressive.")

                return result

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
    scenes = [f"Index {c.get('video_index', i)}: {c.get('scene_type', 'scene')} ({c.get('start', '0')}-{c.get('end', '5')}s, {c.get('clip_duration_sec', 4)}s display) - {c.get('reason', '')}" for i, c in enumerate(timeline)]
    timeline_context = "\n".join(scenes)

    prompt = f"""Property: '{property_name}'
Goal: Generate 3 distinct Reel Variations (Luxury, Instagram Viral, Realtor Style) using the provided Pool of Scenes.
For each variation:
1. Write a hook, description, and hashtags that match the style.
2. Create a custom sequence of video clips by selecting and ordering from the pool of scenes. You can reuse clips, drop clips, or completely change the order to fit the vibe!
   - Luxury: Slower paced, focus on beautiful wide shots, pools, and main rooms.
   - Instagram Viral: Fast-paced, start with the most dramatic/unique shot as the hook, quick cuts.
   - Realtor Style: Traditional logical walkthrough (Exterior -> Entrance -> Living -> Kitchen).

IMPORTANT: For Luxury and Realtor styles, use as many clips as possible from the pool. Only the Viral style should use aggressive quick-cut filtering.

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
