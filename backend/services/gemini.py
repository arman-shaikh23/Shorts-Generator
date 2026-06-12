import os
import asyncio
import json
import time
from google import genai
from google.genai import types

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

async def analyze_and_generate(file_uris: list[str], property_name: str) -> dict:
    """Single Gemini call: analyze multiple videos and build one 20-30s reel."""
    client = get_client()
    start = time.perf_counter()

    prompt = f"""Property: '{property_name}'
Analyze these property videos (in order: index 0 to {len(file_uris)-1}) and select the best scenes (scoring them 1-100) to build ONE highly engaging 20-30 second vertical reel.
Prioritize drone shots, exterior reveals, luxury kitchens, pools, master bedrooms, unique architecture, and premium finishes.
Avoid shaky footage, walking transitions, empty rooms, and repetitive clips.
Return a strict JSON object with 'title', a high-retention 'hook' (e.g., 'Wait until you see the backyard.'), 'hashtags', and a 'timeline' array.
Each timeline scene must specify the 'video_index' (0-indexed matching the order of uploaded videos), 'start' (MM:SS), 'end' (MM:SS), 'scene_type', and 'score' (1-100)."""

    schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "title": types.Schema(type=types.Type.STRING),
            "hook": types.Schema(type=types.Type.STRING),
            "hashtags": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
            "timeline": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "video_index": types.Schema(type=types.Type.INTEGER),
                        "start": types.Schema(type=types.Type.STRING),
                        "end": types.Schema(type=types.Type.STRING),
                        "scene_type": types.Schema(type=types.Type.STRING),
                        "score": types.Schema(type=types.Type.INTEGER),
                    },
                    required=["video_index", "start", "end", "scene_type", "score"]
                )
            )
        },
        required=["title", "hook", "hashtags", "timeline"]
    )

    loop = asyncio.get_event_loop()

    def _generate():
        contents = [types.Part.from_uri(file_uri=uri, mime_type="video/mp4") for uri in file_uris]
        contents.append(prompt)
        
        return client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0.5,
            ),
        )

    response = await loop.run_in_executor(None, _generate)

    elapsed = time.perf_counter() - start
    print(f"[PERF] Gemini analysis+generation: {elapsed:.1f}s")

    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        raise Exception(f"Failed to decode Gemini response as JSON: {response.text}")
