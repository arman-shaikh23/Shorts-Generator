import os
import asyncio
import json
import time
import random
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# --- Startup Diagnostics ---
api_key = os.environ.get("GEMINI_API_KEY", "")
prefix = api_key[:15] if api_key else "NOT_SET"
print("========================================")
print("[STARTUP DIAGNOSTICS] Gemini Analysis Pipeline")
print(f"ACTIVE GEMINI KEY: {prefix}...")
print("SELECTED MODEL: gemini-2.5-flash-lite")
print("BATCH SIZE: 5")
print("RETRY COUNT: 0 (Fast Fail)")
print("========================================")

gemini_semaphore = asyncio.Semaphore(2)

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
    """Upload file to Gemini Files API with exponential backoff polling. Skips FAILED files."""
    client = get_client()
    start = time.perf_counter()
    loop = asyncio.get_event_loop()

    if yield_callback:
        await yield_callback("Uploading preview to Gemini...")

    def _upload():
        return client.files.upload(file=file_path, config={'display_name': display_name})

    upload_retries = 5
    uploaded_file = None
    for attempt in range(upload_retries):
        try:
            uploaded_file = await loop.run_in_executor(None, _upload)
            break
        except Exception as e:
            if attempt == upload_retries - 1:
                print(f"[ERROR] Upload permanently failed for {display_name}: {e}")
                return None
            err_str = str(e)
            if any(code in err_str for code in ["503", "429", "UNAVAILABLE", "500", "502", "504"]):
                print(f"[RETRY] Upload failed with {err_str[:60]}, retrying...")
                await asyncio.sleep(2 * (attempt + 1))
                continue
            print(f"[ERROR] Non-retryable upload error: {e}")
            return None

    upload_elapsed = time.perf_counter() - start
    print(f"[PERF] Gemini upload ({display_name}): {upload_elapsed:.1f}s")

    if yield_callback:
        await yield_callback("Preview uploaded. Waiting for Gemini processing...")

    poll_start = time.perf_counter()
    delay = 2.0
    max_delay = 10.0
    poll_count = 0

    while True:
        def _get_file():
            return client.files.get(name=uploaded_file.name)

        try:
            file_info = await loop.run_in_executor(None, _get_file)
        except Exception as e:
            err_str = str(e)
            if any(code in err_str for code in ["503", "429", "UNAVAILABLE", "500", "502", "504", "404"]):
                print(f"[RETRY] Polling failed with {err_str[:60]}, waiting...")
                await asyncio.sleep(delay)
                delay = min(delay * 1.5, max_delay)
                continue
            print(f"[ERROR] Polling aborted for {display_name}: {e}")
            return None

        poll_count += 1
        if file_info.state == "ACTIVE":
            break
        elif file_info.state == "FAILED":
            print(f"[ERROR] Gemini file processing FAILED for {display_name} (URI: {file_info.uri})")
            return None

        await asyncio.sleep(delay)
        delay = min(delay * 1.5, max_delay)

    poll_elapsed = time.perf_counter() - poll_start
    total_elapsed = time.perf_counter() - start
    print(f"[PERF] Gemini poll ({display_name}): {poll_elapsed:.1f}s ({poll_count} polls)  |  Total: {total_elapsed:.1f}s")

    if yield_callback:
        await yield_callback("Video processing complete.")

    return file_info


async def _analyze_batch(batch_infos: list, prompt: str, schema: types.Schema, yield_callback=None, batch_num: int = 1, total_batches: int = 1) -> dict:
    client = get_client()
    loop = asyncio.get_event_loop()
    
    models = ['gemini-2.5-flash-lite', 'gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-2.5-pro']
    file_names = [f.name for f in batch_infos]
    prompt_len = len(prompt)
    
    for model_name in models:
        max_retries = 1
        backoff_schedule = [5]
        
        async with gemini_semaphore:
            for attempt in range(max_retries):
                start_attempt = time.perf_counter()
                try:
                    def _generate():
                        contents = list(batch_infos)
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
                    
                    print(f"ACTIVE GEMINI KEY: {os.environ.get('GEMINI_API_KEY', 'UNKNOWN')[:15]}...")
                    print(f"[VIDEO START] BATCH={batch_num} | MODEL={model_name} | VIDEOS={len(batch_infos)} | PROMPT_LENGTH={prompt_len} | FILES={file_names}")
                    
                    future = loop.run_in_executor(None, _generate)
                    response = await asyncio.wait_for(future, timeout=90.0)
                    
                    elapsed = time.perf_counter() - start_attempt
                    print(f"[VIDEO SUCCESS] Gemini {model_name} success on attempt {attempt+1}: {elapsed:.1f}s")
                    
                    text = response.text
                    if text.startswith("```json"):
                        text = text[7:-3]
                        
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        raise Exception(f"Failed to decode Gemini response as JSON. Excerpt: {text[:100]}")
                        
                except asyncio.TimeoutError:
                    print(f"[VIDEO TIMEOUT] BATCH={batch_num} | MODEL={model_name} | Hung for >90s. Aborting.")
                    print(f"[VIDEO FALLBACK] Switching to next fallback model...")
                    break # Break retry loop, try next model immediately
                except Exception as e:
                    error_str = str(e)
                    err_type = type(e).__name__
                    
                    if any(term in error_str for term in ["GenerateRequestsPerDay", "generate_content_free_tier", "quota exceeded", "RESOURCE_EXHAUSTED", "429"]):
                        print(f"[QUOTA EXHAUSTED] BATCH={batch_num} | MODEL={model_name} | ERROR={error_str[:150]}")
                        last_error_was_quota = True
                        break # Break retry loop, try next model immediately

                    last_error_was_quota = False
                    is_timeout = isinstance(e, asyncio.TimeoutError)
                    is_retryable = is_timeout or any(code in error_str for code in ["429", "500", "502", "503", "504", "UNAVAILABLE", "Model overloaded", "overloaded"])
                    
                    elapsed = time.perf_counter() - start_attempt
                    
                    print(f"[ERROR] BATCH={batch_num} | MODEL={model_name} | VIDEOS={len(batch_infos)} | PROMPT_LENGTH={prompt_len} | ERROR_TYPE={err_type} | ERROR={error_str}")
                    
                    if not is_retryable or attempt == max_retries - 1:
                        print(f"[WARN] Exhausted retries or non-retryable error for {model_name}. Moving to fallback model if available.")
                        print(f"[VIDEO FALLBACK] Switching to next fallback model...")
                        break
                        
                    base_delay = backoff_schedule[attempt]
                    jitter = random.uniform(0, 3)
                    delay = base_delay + jitter
                    
                    # Extract Google's exact requested delay if present
                    import re
                    match = re.search(r'Please retry in ([\d\.]+)s', error_str)
                    if match:
                        delay = float(match.group(1)) + 1.5
                        print(f"[RATE LIMIT] Google API requested exact delay. Using {delay:.1f}s")
                        
                    print(f"[RETRY] Model: {model_name}. Delaying {delay:.1f}s")
                    
                    if yield_callback:
                        await yield_callback(f"API Rate Limit hit, waiting {int(delay)}s... ({model_name})")
                    await asyncio.sleep(delay)
                    
    # If we get here and last_error_was_quota is True, ALL models are exhausted!
    if 'last_error_was_quota' in locals() and locals()['last_error_was_quota']:
        raise Exception("Gemini quota exhausted across ALL models. Please wait for quota reset or use a billing-enabled project.")

    # Isolation Logic
    if len(batch_infos) > 1:
        print(f"[ISOLATION] Batch {batch_num} failed on ALL models. Splitting batch into two halves to isolate toxic video...")
        mid = len(batch_infos) // 2
        half1 = batch_infos[:mid]
        half2 = batch_infos[mid:]
        
        res1 = await _analyze_batch(half1, prompt, schema, yield_callback, batch_num, total_batches)
        res2 = await _analyze_batch(half2, prompt, schema, yield_callback, batch_num, total_batches)
        
        merged = {"selected_clips": []}
        if res1 and "selected_clips" in res1:
            merged["selected_clips"].extend(res1["selected_clips"])
        if res2 and "selected_clips" in res2:
            merged["selected_clips"].extend(res2["selected_clips"])
        return merged
    else:
        toxic_name = batch_infos[0].name if batch_infos else "Unknown"
        print(f"[TOXIC VIDEO ISOLATED] Skipping problematic video automatically: {toxic_name}")
        return {"selected_clips": []}


async def analyze_and_generate(file_infos: list, property_name: str, duration: str, style: str, duplicate_sensitivity: str = "Low", yield_callback=None) -> dict:
    total_clip_count = len(file_infos)
    BATCH_SIZE = 8
    batches = [file_infos[i:i + BATCH_SIZE] for i in range(0, total_clip_count, BATCH_SIZE)]
    
    schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "selected_clips": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "video_index": types.Schema(type=types.Type.INTEGER),
                        "scene_type": types.Schema(type=types.Type.STRING),
                        "start": types.Schema(type=types.Type.STRING),
                        "end": types.Schema(type=types.Type.STRING),
                        "hero_score": types.Schema(type=types.Type.INTEGER),
                        "composition_score": types.Schema(type=types.Type.INTEGER),
                        "hook_score": types.Schema(type=types.Type.INTEGER),
                        "luxury_score": types.Schema(type=types.Type.INTEGER),
                        "camera_motion": types.Schema(type=types.Type.STRING),
                        "camera_direction": types.Schema(type=types.Type.STRING),
                        "shot_size": types.Schema(type=types.Type.STRING)
                    },
                    required=["video_index", "scene_type", "start", "end", "hero_score", "composition_score", "hook_score", "luxury_score", "camera_motion", "camera_direction", "shot_size"]
                )
            )
        },
        required=["selected_clips"]
    )
    
    prompt = f"""Property: '{property_name}'
Analyze the attached videos. Extract the most stunning cinematic scenes.
Focus purely on aesthetics, framing, and content. (Physical camera shake is handled by an external computer vision pipeline, so assume clips can be trimmed for stability later).

Reel Goals:
- Build the longest high-quality cinematic timeline possible. 
- NEVER remove a good clip just to make the reel shorter.
- Select segments between 4 and 12 seconds depending on their aesthetic quality.

Return an array of 'selected_clips'.
For each clip:
- 'video_index': The exact index of the video (0 for the first video in this batch, 1 for the second, etc.)
- 'scene_type': Strict labels (e.g., 'drone', 'aerial', 'exterior', 'lobby', 'living_room', 'kitchen', 'bedroom', 'bathroom', 'pool', 'gym', 'garden', 'parking', 'amenities'). 
  CRITICAL: Drone/DJI footage must NEVER be classified as interior rooms (kitchen/bedroom/etc.). It can ONLY be drone, aerial, exterior, pool, garden, or amenities.
- 'start' and 'end': Timestamps in seconds.
- 'hero_score': 0-100 score based on visual appeal. (100-90: Luxury, Premium. 89-70: Good but not exceptional. Below 70: Avoid).
- 'composition_score': 0-100 score evaluating framing, rule of thirds, and architectural lines.
- 'hook_score': 0-100 score for how well the shot works as an opening hook.
- 'luxury_score': 0-100 score for how luxurious the shot feels (high-end aesthetics).
- 'camera_motion': Choose from: static, push_in, push_out, pan, orbit, tilt.
- 'camera_direction': Choose from: left_to_right, right_to_left, forward, backward, neutral.
- 'shot_size': Choose from: wide, medium, close.

Avoid selecting visually similar clips. Keep only the strongest angles.
"""

    all_selected_clips = []
    
    for batch_idx, batch_infos in enumerate(batches):
        offset = batch_idx * BATCH_SIZE
        if yield_callback:
            await yield_callback(f"Vision Analysis: Batch {batch_idx+1}/{len(batches)}...")
            
        result = await _analyze_batch(batch_infos, prompt, schema, yield_callback, batch_idx+1, len(batches))
        
        for clip in result.get("selected_clips", []):
            clip["video_index"] += offset
            all_selected_clips.append(clip)
            
    # Text Generation Call
    text_prompt = f"""Property: '{property_name}'
Style: {style}
Scenes identified: {[c.get("scene_type") for c in all_selected_clips]}

Generate metadata for a real estate reel using these scenes.
"""
    text_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "property_type": types.Schema(type=types.Type.STRING),
            "title": types.Schema(type=types.Type.STRING),
            "hook": types.Schema(type=types.Type.STRING),
            "description": types.Schema(type=types.Type.STRING),
            "hashtags": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
        },
        required=["property_type", "title", "hook", "description", "hashtags"]
    )
    
    text_result = {}
    if yield_callback:
        await yield_callback("Generating textual metadata...")
        
    client = get_client()
    text_models = ['gemini-2.5-flash-lite', 'gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-2.5-pro']
    
    for t_model in text_models:
        try:
            print(f"[TEXT START] Generating metadata with {t_model}")
            def _gen_text():
                print(f"ACTIVE GEMINI KEY: {os.environ.get('GEMINI_API_KEY', 'UNKNOWN')[:15]}...")
                return client.models.generate_content(
                    model=t_model,
                    contents=text_prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=text_schema)
                )
            future = asyncio.get_event_loop().run_in_executor(None, _gen_text)
            res = await asyncio.wait_for(future, timeout=90.0)
            text = res.text
            if text.startswith("```json"): text = text[7:-3]
            text_result = json.loads(text)
            print(f"[TEXT SUCCESS] Metadata generated successfully on {t_model}")
            break # Success
        except asyncio.TimeoutError:
            print(f"[TEXT TIMEOUT] Model {t_model} hung for >90s! Aborting request.")
            print(f"[TEXT FALLBACK] Switching to next fallback model...")
        except Exception as e:
            print(f"[ERROR] Text generation failed on {t_model}: {e}")
            print(f"[TEXT FALLBACK] Switching to next fallback model...")
        
    return {
        "property_type": text_result.get("property_type", "Real Estate"),
        "title": text_result.get("title", property_name),
        "hook": text_result.get("hook", ""),
        "description": text_result.get("description", ""),
        "hashtags": text_result.get("hashtags", []),
        "selected_clips": all_selected_clips,
        "total_analyzed_duration_sec": 0,
        "total_selected_duration_sec": 0  # Computed safely in Python later
    }

async def generate_variations(property_name: str, timeline: list) -> dict:
    """Phase 2: Generate distinct text variations based on the timeline."""
    client = get_client()

    scenes = [f"Index {c.get('video_index', i)}: {c.get('scene_type', 'scene')} ({c.get('start', '0')}-{c.get('end', '5')}s) - Score: {c.get('hero_score', 0)}" for i, c in enumerate(timeline)]
    timeline_context = "\n".join(scenes)

    prompt = f"""Property: '{property_name}'
Goal: Generate 3 distinct Reel Variations (Luxury, Instagram Viral, Realtor Style).
Pool of Scenes:
{timeline_context}

For each variation, select 'custom_sequence' referencing the Index values to define the sequence.
"""

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
    
    var_models = ['gemini-2.5-flash-lite', 'gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-2.5-pro']
    last_error = None
    
    for v_model in var_models:
        def _generate():
            print(f"ACTIVE GEMINI KEY: {os.environ.get('GEMINI_API_KEY', 'UNKNOWN')[:15]}...")
            return client.models.generate_content(
                model=v_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.5,
                )
            )

        await gemini_semaphore.acquire()
        try:
            print(f"[TEXT START] Generating variations with {v_model}")
            future = loop.run_in_executor(None, _generate)
            response = await asyncio.wait_for(future, timeout=90.0)
            text = response.text
            if text.startswith("```json"):
                text = text[7:-3]
            print(f"[TEXT SUCCESS] Variations generated successfully on {v_model}")
            return json.loads(text)
        except asyncio.TimeoutError:
            print(f"[TEXT TIMEOUT] Model {v_model} hung for >90s! Aborting request.")
            print(f"[TEXT FALLBACK] Switching to next fallback model...")
            last_error = Exception("Timeout on all models")
        except Exception as e:
            print(f"[ERROR] Gemini variations generation failed on {v_model}: {e}")
            print(f"[TEXT FALLBACK] Switching to next fallback model...")
            last_error = e
        finally:
            gemini_semaphore.release()
            
    raise last_error
