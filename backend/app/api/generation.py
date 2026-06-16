from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
import asyncio
import time
from sse_starlette.sse import EventSourceResponse
import logging
import json

from ..core.database import get_db
from ..core.dependencies import get_current_user
from services.gemini import upload_and_wait, analyze_and_generate, generate_variations
from services.video import build_reel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/generation", tags=["Generation"])

# ── Helpers ─────────────────────────────────────────────

SCENE_ORDER = [
    "drone", "aerial", "exterior", "property_sign", "entrance", "lobby",
    "living room", "living_room", "dining", "kitchen",
    "bedroom", "bathroom",
    "balcony", "pool", "gym", "garden", "parking", "amenities", "amenity",
    "closing drone", "closing"
]

OPENING_ALLOWED = {"drone", "aerial", "exterior", "living room", "living_room", "pool", "lobby"}
OPENING_BANNED = {"bathroom", "parking", "utility", "storage", "garage", "corridor", "hallway"}

def _parse_target_duration(duration: str) -> int:
    """Parse duration string to target seconds."""
    if "min" in duration.lower():
        if "5 min" in duration: return 300
        elif "4 min" in duration: return 240
        elif "3 min" in duration: return 180
        elif "2 min" in duration: return 120
        elif "1 min" in duration: return 60
        return 120  # Default YouTube: 2 min
    else:
        if "60" in duration: return 60
        elif "45" in duration: return 45
        elif "30" in duration: return 30
        elif "20" in duration: return 20
        return 60  # Default Shorts: 60s

def _get_scene_order_key(scene_type: str) -> int:
    """Get ordering key for a scene type."""
    st = scene_type.lower().strip()
    for i, val in enumerate(SCENE_ORDER):
        if val == st:
            return i
    return 99  # Unknown scenes go to end

def _is_bad_opening(scene_type: str) -> bool:
    """Check if a scene type is inappropriate for opening."""
    st = scene_type.lower().strip().replace("_", " ")
    for banned in OPENING_BANNED:
        if banned in st:
            return True
    return False

def _is_good_opening(scene_type: str) -> bool:
    """Check if a scene type is good for opening."""
    st = scene_type.lower().strip().replace("_", " ")
    for allowed in OPENING_ALLOWED:
        if allowed in st:
            return True
    return False

def _fix_timeline(timeline: list[dict]) -> list[dict]:
    """Post-process timeline to fix sequence and opening."""
    if not timeline:
        return timeline
    
    fixed = list(timeline)
    
    # 1. Fix opening: if first clip is banned, swap with a good one
    first = fixed[0]
    if _is_bad_opening(first.get("scene_type", "")):
        # Find first good opening clip
        for i, clip in enumerate(fixed):
            if _is_good_opening(clip.get("scene_type", "")):
                fixed[0], fixed[i] = fixed[i], fixed[0]
                logger.info(f"[FIX] Swapped opening clip: was '{first.get('scene_type')}', now '{fixed[0].get('scene_type')}'")
                break
    
    # 2. Sort by scene order for logical walkthrough
    # Group clips by their relative order, preserving the original sequence otherwise
    fixed.sort(key=lambda c: _get_scene_order_key(c.get("scene_type", "")))
    
    # 3. Ensure opening is still first (it should be since OPENING role has lowest order key)
    # But double-check: if no clip has role=OPENING, make sure first clip is not banned
    if fixed and _is_bad_opening(fixed[0].get("scene_type", "")):
        for i, clip in enumerate(fixed):
            if _is_good_opening(clip.get("scene_type", "")):
                fixed[0], fixed[i] = fixed[i], fixed[0]
                break
    
    return fixed


# ── Request Models ──────────────────────────────────────

class AnalyzeRequest(BaseModel):
    duration: str = "30 sec"
    style: str = "Luxury"

class GenerateRequest(BaseModel):
    timeline: list[dict]
    duration: str = "30 sec"
    style: str = "Luxury"

# ── Endpoints ───────────────────────────────────────────

@router.get("/analyze")
async def analyze_project(
    project_id: str, 
    request: Request,
    duration: str = "30 sec",
    style: str = "Luxury",
    duplicate_sensitivity: str = "Low",
    user = Depends(get_current_user)
):
    """Phase 1: Ask Gemini to propose a sequence using the uploaded previews. Uses SSE for progress."""
    db = get_db()
    
    project = await db.projects.find_one({"_id": ObjectId(project_id), "userId": user["_id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    q = asyncio.Queue()

    async def sse_generator():
        try:
            # 1. Fetch all PROCESSED uploads and DUPLICATE uploads
            cursor = db.uploads.find({"projectId": project_id, "status": "PROCESSED"}).sort("order", 1)
            uploads = []
            async for doc in cursor:
                uploads.append(doc)

            dup_cursor = db.uploads.find({"projectId": project_id, "status": "DUPLICATE"})
            pre_duplicates = []
            async for doc in dup_cursor:
                pre_duplicates.append(doc)

            if len(uploads) < 3:
                await q.put({"status": "error", "message": f"Need at least 3 processed clips. Found {len(uploads)}."})
                return

            await q.put({"status": "progress", "message": f"Found {len(uploads)} processed clips and intercepted {len(pre_duplicates)} exact duplicates. Uploading to AI..."})

            # 2. Upload previews to Gemini sequentially to track progress
            file_infos = [None] * len(uploads)
            total = sum(1 for u in uploads if u.get("previewPath"))
            completed = 0
            
            await q.put({"status": "progress", "message": f"Uploading clips to AI Engine (0/{total} done)..."})
            
            async def track_upload(i, up):
                info = await upload_and_wait(up["previewPath"], f"{project['title']}_part{i}")
                return i, info

            tasks = [track_upload(i, up) for i, up in enumerate(uploads) if up.get("previewPath")]
            
            for coro in asyncio.as_completed(tasks):
                idx, info = await coro
                file_infos[idx] = info
                completed += 1
                await q.put({"status": "progress", "message": f"Uploading clips to AI Engine ({completed}/{total} done)..."})

            file_infos_clean = [info for info in file_infos if info is not None]

            # 3. Gemini Analysis
            await q.put({"status": "progress", "message": "Detecting Scenes..."})
            await asyncio.sleep(0.5)
            await q.put({"status": "progress", "message": "Classifying Property Type..."})
            await asyncio.sleep(0.5)
            await q.put({"status": "progress", "message": "Ranking Clips..."})
            await asyncio.sleep(0.5)
            await q.put({"status": "progress", "message": "Building Storyline..."})

            async def yield_message(msg: str):
                await q.put({"status": "progress", "message": msg})

            gemini_result = await analyze_and_generate(file_infos_clean, project["title"], duration, style, duplicate_sensitivity, yield_callback=yield_message)

            # Map the Gemini result to the actual upload objects
            timeline = gemini_result.get("selected_clips", [])
            mapped_timeline = []
            for c in timeline:
                idx = c.get("video_index", 0)
                if idx < len(uploads):
                    c["upload_id"] = str(uploads[idx]["_id"])
                    c["localPath"] = uploads[idx].get("localPath")
                    mapped_timeline.append(c)

            # ── PYTHON BUSINESS LOGIC: DUPLICATE DETECTION & CATEGORY LIMITS ──
            seen_upload_scenes = set()
            scene_counts = {}
            deduplicated = []
            ai_removed = []
            
            for c in mapped_timeline:
                stype = c.get("scene_type", "").lower()
                upload_id = c.get("upload_id")
                
                key = f"{upload_id}_{stype}"
                
                if key in seen_upload_scenes:
                    ai_removed.append({"video_index": c.get("video_index"), "reason": f"Python Deduplication: Already selected {stype} from this specific video."})
                    continue
                
                scene_counts[stype] = scene_counts.get(stype, 0) + 1
                if scene_counts[stype] > 2:
                    ai_removed.append({"video_index": c.get("video_index"), "reason": f"Python Category Limit: Already have enough {stype} scenes."})
                    continue
                    
                seen_upload_scenes.add(key)
                deduplicated.append(c)

            # ── PYTHON BUSINESS LOGIC: SORTING ──
            # Sort chronologically by property tour role, tie-break by hero_score
            deduplicated.sort(key=lambda c: (_get_scene_order_key(c.get("scene_type", "")), -int(c.get("hero_score", 0))))

            # ── POST-PROCESSING: Fix timeline sequence and opening ──
            timeline = _fix_timeline(deduplicated)

            # Update final_order to match the fixed timeline
            gemini_result["final_order"] = [c.get("video_index") for c in timeline]
            gemini_result["selected_clips"] = timeline
            gemini_result["timeline"] = timeline
            
            # Use 'end' - 'start' to compute duration since clip_duration_sec is gone
            total_sec = 0
            
            def parse_time(t):
                if isinstance(t, (int, float)): return float(t)
                t = str(t).strip()
                if ":" in t:
                    parts = t.split(":")
                    if len(parts) == 3: return float(parts[0])*3600 + float(parts[1])*60 + float(parts[2])
                    if len(parts) == 2: return float(parts[0])*60 + float(parts[1])
                try:
                    return float(t)
                except:
                    return 0.0

            for c in timeline:
                start_val = parse_time(c.get("start", 0))
                end_val = parse_time(c.get("end", 5))
                # Ensure they are safely overwritten as strings or numbers that FFmpeg understands
                c["start"] = start_val
                c["end"] = end_val
                dur = end_val - start_val
                if dur <= 0: dur = 4.0
                c["clip_duration_sec"] = dur
                total_sec += dur
                
            gemini_result["total_selected_duration_sec"] = total_sec
            gemini_result["removed_clips"] = ai_removed

            logger.info(f"[POST-PROCESS] Fixed timeline: {len(timeline)} clips, total {gemini_result['total_selected_duration_sec']:.0f}s")

            # Save the timeline and AI metadata to the project
            coverage = gemini_result.get("coverage_analytics", {})
            
            # Combine AI removed clips with Pre-processor removed clips
            ai_removed = gemini_result.get("removed_clips", [])
            all_removed = ai_removed.copy()
            for dup in pre_duplicates:
                all_removed.append({
                    "video_index": -1, # Pre-processor blocked
                    "reason": dup.get("duplicateReason", "Pre-Processor Exact Match")
                })
                
            total_uploaded = len(uploads) + len(pre_duplicates)
            total_removed = len(ai_removed) + len(pre_duplicates)

            ai_metadata = {
                "analyzed_sec": gemini_result.get("total_analyzed_duration_sec", 0),
                "selected_sec": gemini_result.get("total_selected_duration_sec", 0),
                "duplicates_removed": total_removed,
                "removed_clips": all_removed,
                "coverage_analytics": {
                    "uploaded_count": total_uploaded,
                    "pre_processor_duplicates": len(pre_duplicates),
                    "ai_duplicates": len(ai_removed),
                    "duplicates_removed": total_removed,
                    "selected_count": coverage.get("selected_count", len(timeline)),
                    "coverage_percentage": coverage.get("coverage_percentage", 0)
                }
            }
            await db.projects.update_one(
                {"_id": ObjectId(project_id)},
                {"$set": {
                    "draftTimeline": timeline, 
                    "status": "ANALYZED",
                    "aiMetadata": ai_metadata
                }}
            )

            await q.put({"status": "completed", "results": [gemini_result]})

        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            await q.put({"status": "error", "message": str(e)})

    async def event_publisher():
        task = asyncio.create_task(sse_generator())
        try:
            while True:
                if await request.is_disconnected():
                    task.cancel()
                    break
                try:
                    data = await asyncio.wait_for(q.get(), timeout=1.0)
                    yield {"data": json.dumps(data)}
                    if data["status"] in ["completed", "error"]:
                        break
                except asyncio.TimeoutError:
                    continue
        except asyncio.CancelledError:
            task.cancel()

    return EventSourceResponse(event_publisher())


@router.get("/generate")
async def generate_project(
    project_id: str, 
    request: Request,
    duration: str = "30 sec",
    style: str = "Luxury",
    aspect_ratio: str = "9:16",
    music_path: Optional[str] = None,
    music_volume: float = 0.2,
    vo_volume: float = 1.0,
    user = Depends(get_current_user)
):
    """Phase 2: Render the final reel using the approved timeline."""
    db = get_db()
    
    project = await db.projects.find_one({"_id": ObjectId(project_id), "userId": user["_id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    timeline = project.get("draftTimeline")
    if not timeline:
        raise HTTPException(status_code=400, detail="Project has no analyzed timeline. Run analysis first.")

    q = asyncio.Queue()

    async def sse_generator():
        try:
            await q.put({"status": "progress", "message": "Generating 3 AI text variations..."})
            
            # Phase 2: Generate 3 variations using Gemini
            try:
                variations_data = await generate_variations(project["title"], timeline)
                variations = variations_data.get("variations", [])
                if len(variations) == 0:
                    raise Exception("Gemini returned empty variations.")
            except Exception as e:
                logger.error(f"Failed to generate variations: {e}")
                # Fallback to single variation if Gemini fails
                variations = [{
                    "style": style,
                    "hook": "Check out this beautiful property!",
                    "description": "Welcome to your dream home.",
                    "hashtags": ["#realestate", "#property"]
                }]

            # Fetch local paths for the timeline
            input_paths = []
            for item in timeline:
                upload_id = item.get("upload_id")
                if upload_id:
                    upload = await db.uploads.find_one({"_id": ObjectId(upload_id)})
                    if upload and upload.get("localPath"):
                        input_paths.append(upload["localPath"])

            if not input_paths:
                await q.put({"status": "error", "message": "No local video paths found for the timeline."})
                return

            target_duration = _parse_target_duration(duration)

            results = []

            for i, var in enumerate(variations):
                var_style = var.get("style", style)
                await q.put({"status": "progress", "message": f"Rendering {var_style} variation ({i+1}/{len(variations)})..."})
                
                # Build custom timeline for this variation
                custom_seq = var.get("custom_sequence", [])
                var_timeline = []
                timeline_map = {block.get("video_index"): block for block in timeline}
                
                for idx in custom_seq:
                    if idx in timeline_map:
                        var_timeline.append(timeline_map[idx])
                
                # Fallback to original timeline if custom_sequence failed
                if not var_timeline:
                    var_timeline = timeline

                # Render video for this variation
                output_path = await build_reel(
                    timeline_blocks=var_timeline,
                    input_paths=input_paths,
                    property_name=project["title"],
                    target_duration_sec=target_duration,
                    style=var_style,
                    project_id=project_id,
                    aspect_ratio=aspect_ratio,
                    music_path=music_path,
                    music_volume=music_volume,
                    vo_volume=vo_volume
                )

                web_url = "/" + output_path.replace("\\", "/")
                
                # Get actual output duration
                try:
                    from services.video import get_exact_duration
                    actual_dur_sec = await asyncio.to_thread(get_exact_duration, output_path)
                    actual_duration_str = f"{int(actual_dur_sec)}s"
                except Exception as e:
                    logger.warning(f"Failed to get exact duration: {e}")
                    actual_duration_str = duration

                # Save to generated shorts
                short = {
                    "projectId": project_id,
                    "userId": user["_id"],
                    "videoUrl": web_url,
                    "duration": actual_duration_str,
                    "style": var_style,
                    "format": aspect_ratio,
                    "hook": var.get("hook", ""),
                    "description": var.get("description", ""),
                    "hashtags": var.get("hashtags", []),
                    "createdAt": time.time()
                }
                await db.generated_shorts.insert_one(short)
                
                # We return the _id so the frontend can use it if needed, but we stringify it
                short["_id"] = str(short["_id"])
                
                # Make sure projectId and userId are also strings if we return them
                short["projectId"] = str(short["projectId"])
                short["userId"] = str(short["userId"])
                
                results.append(short)

                # Update project generated count
                await db.projects.update_one(
                    {"_id": ObjectId(project_id)},
                    {"$set": {"status": "COMPLETED"}, "$inc": {"generatedCount": 1}}
                )

            await q.put({"status": "completed", "results": results})

        except Exception as e:
            logger.error(f"Generation error: {e}", exc_info=True)
            await q.put({"status": "error", "message": str(e)})

    async def event_publisher():
        task = asyncio.create_task(sse_generator())
        try:
            while True:
                if await request.is_disconnected():
                    task.cancel()
                    break
                try:
                    data = await asyncio.wait_for(q.get(), timeout=1.0)
                    yield {"data": json.dumps(data)}
                    if data["status"] in ["completed", "error"]:
                        break
                except asyncio.TimeoutError:
                    continue
        except asyncio.CancelledError:
            task.cancel()

    return EventSourceResponse(event_publisher())
