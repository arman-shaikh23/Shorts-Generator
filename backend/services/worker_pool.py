import asyncio
import os
import base64
import json
import logging
import time
from typing import List, Dict, Any, Optional

try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

def encode_image(img_path):
    with open(img_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

async def analyze_scene_groq(client, keyframe_path: str, retries: int = 3) -> Dict[str, Any]:
    base64_image = encode_image(keyframe_path)
    prompt = """Analyze this real estate scene. 
Return ONLY strict JSON with these keys:
- 'scene_type': string (e.g. exterior, kitchen, pool, bathroom, living room, bedroom, drone, amenities)
- 'visual_quality_score': int (0-100, sharpness, lighting, framing)
- 'luxury_appeal': int (0-100)
- 'has_people': boolean
- 'confidence_score': int (0-100, confidence in scene type)
- 'reason': string (brief 1 sentence description)"""

    for attempt in range(retries):
        try:
            res = await client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                temperature=0.2,
                max_completion_tokens=256,
                response_format={"type": "json_object"}
            )
            return json.loads(res.choices[0].message.content)
        except Exception as e:
            if attempt == retries - 1:
                logger.error(f"Groq API failed on {keyframe_path}: {e}")
                raise e
            await asyncio.sleep(1 + attempt)

async def analyze_scene_gemini(client, keyframe_path: str, retries: int = 3) -> Dict[str, Any]:
    prompt = """Analyze this real estate scene. Classify it (e.g. exterior, kitchen, pool, bathroom, living room, bedroom, drone, amenities). Score visual quality (0-100) and luxury appeal (0-100). Detect if people are present. Give confidence score (0-100) and a brief reason."""
    
    schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "scene_type": types.Schema(type=types.Type.STRING),
            "visual_quality_score": types.Schema(type=types.Type.INTEGER),
            "luxury_appeal": types.Schema(type=types.Type.INTEGER),
            "has_people": types.Schema(type=types.Type.BOOLEAN),
            "confidence_score": types.Schema(type=types.Type.INTEGER),
            "reason": types.Schema(type=types.Type.STRING)
        },
        required=["scene_type", "visual_quality_score", "luxury_appeal", "has_people", "confidence_score", "reason"]
    )
    
    loop = asyncio.get_event_loop()
    
    for attempt in range(retries):
        try:
            def _generate():
                return client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=[types.Part.from_bytes(data=open(keyframe_path, 'rb').read(), mime_type='image/jpeg'), prompt],
                    config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=schema, temperature=0.2)
                )
            response = await loop.run_in_executor(None, _generate)
            return json.loads(response.text)
        except Exception as e:
            if attempt == retries - 1:
                logger.error(f"Gemini Fallback failed on {keyframe_path}: {e}")
                return {"scene_type": "unknown", "visual_quality_score": 0, "luxury_appeal": 0, "has_people": False, "confidence_score": 0, "reason": "API Failure"}
            await asyncio.sleep(1 + attempt)

async def worker(queue: asyncio.Queue, results_list: List[Dict], groq_client, gemini_client, progress_cb: Optional[callable] = None):
    while True:
        task = await queue.get()
        if task is None:
            queue.task_done()
            break
            
        scene_meta = task['scene']
        
        # Primary: Groq. Fallback: Gemini
        ai_res = None
        if groq_client:
            try:
                ai_res = await analyze_scene_groq(groq_client, scene_meta['keyframe_path'])
            except Exception:
                ai_res = None
                
        if not ai_res and gemini_client:
            ai_res = await analyze_scene_gemini(gemini_client, scene_meta['keyframe_path'])
            
        if not ai_res:
            ai_res = {"scene_type": "unknown", "visual_quality_score": 0, "luxury_appeal": 0, "has_people": False, "confidence_score": 0, "reason": "All APIs failed"}
            
        # Hybrid Scoring: Combine AI Visual Score + Local Blur Score + Temporal Duration Factor
        # Local Blur score < 100 is blurry.
        local_blur = scene_meta.get('blur_score', 0.0)
        ai_qual = ai_res.get('visual_quality_score', 0)
        
        # Normalize blur to 0-100 scale roughly (Laplacian variance > 500 is very sharp)
        norm_blur = min((local_blur / 300.0) * 100.0, 100.0)
        
        # Hybrid Score = 60% AI Visual + 40% Objective Blur
        hybrid_score = int((ai_qual * 0.6) + (norm_blur * 0.4))
        ai_res['hybrid_quality_score'] = hybrid_score
        
        final_res = {**scene_meta, **ai_res}
        results_list.append(final_res)
        
        if progress_cb:
            await progress_cb(final_res)
            
        queue.task_done()

async def process_scenes_parallel(scenes: List[Dict], concurrency: int = 8, progress_cb: Optional[callable] = None) -> List[Dict]:
    """Process a list of scene metadata dicts concurrently via AI."""
    start = time.perf_counter()
    groq_key = os.environ.get("GROQ_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    groq_client = AsyncGroq(api_key=groq_key) if groq_key and AsyncGroq else None
    gemini_client = genai.Client(api_key=gemini_key) if gemini_key else None
    
    if not groq_client and not gemini_client:
        raise ValueError("No AI Providers configured (missing API keys).")

    queue = asyncio.Queue()
    results = []
    
    for s in scenes:
        queue.put_nowait({"scene": s})
        
    for _ in range(concurrency):
        queue.put_nowait(None)
        
    workers = [asyncio.create_task(worker(queue, results, groq_client, gemini_client, progress_cb)) for _ in range(concurrency)]
    
    await asyncio.gather(*workers)
    
    elapsed = time.perf_counter() - start
    logger.info(f"[PERF] Parallel processed {len(scenes)} scenes in {elapsed:.1f}s")
    
    return results
