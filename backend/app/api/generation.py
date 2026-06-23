from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
import asyncio
import time
from sse_starlette.sse import EventSourceResponse
import logging
import json
from collections import Counter

from ..core.config import get_settings
from ..core.cache import (
    invalidate_after_generation_mutation,
    invalidate_after_project_mutation,
)
from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..core.mongo_utils import parse_object_id
from services.gemini import upload_and_wait, analyze_and_generate, generate_variations
from services.video import build_reel
from services.cv_analyzer import analyze_video_segment, detect_camera_adjustments, cv_semaphore
from services.quality_v2 import analyze_stability_v2, recommend_trim_bounds_v2
from services.timeline_optimizer import parse_time, build_highlight_memory

import os
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
    project_oid = parse_object_id(project_id, "project_id")
    
    project = await db.projects.find_one({"_id": project_oid, "userId": user["_id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    settings = get_settings()
    quality_options = {
        "shadow_mode": settings.PIPELINE_SHADOW_MODE,
        "enable_story_v2": settings.ENABLE_STORY_V2,
        "enable_scoring_v2": settings.ENABLE_SCORING_V2,
        "enable_dedup_v2": settings.ENABLE_DEDUP_V2,
        "min_story_confidence": settings.V2_MIN_STORY_CONFIDENCE,
        "stability_weight": settings.V2_STABILITY_WEIGHT,
        "cinematic_weight": settings.V2_CINEMATIC_WEIGHT,
        "story_weight": settings.V2_STORY_WEIGHT,
        "room_uniqueness_weight": settings.V2_ROOM_UNIQUENESS_WEIGHT,
        "transition_weight": settings.V2_TRANSITION_WEIGHT,
    }

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

            if len(uploads) < 1:
                await q.put({"status": "error", "message": f"Need at least 1 processed clip. Found {len(uploads)}."})
                return

            await q.put({"status": "progress", "message": f"Found {len(uploads)} processed clips and intercepted {len(pre_duplicates)} exact duplicates. Uploading to AI..."})

            # 2. Upload previews to Gemini sequentially to track progress
            logger.info(f"[DEBUG] Total uploads: {len(uploads)}")
            for i, upload in enumerate(uploads):
                logger.info(
                    f"[UPLOAD {i}] "
                    f"id={upload.get('_id')} "
                    f"path={upload.get('localPath')} "
                    f"preview={upload.get('previewPath')}"
                )
                
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

            # ── V4.0 POST-PROCESSING: Cinematic Timeline Optimizer ──
            from services.timeline_optimizer import TimelineOptimizer
            ai_removed = []
            
            # Map the Gemini result to the actual upload objects and Run CV Analysis
            timeline = gemini_result.get("selected_clips", [])
            
            logger.info(f"[GEMINI] Selected {len(timeline)} clips")
            for clip in timeline:
                logger.info(
                    f"[GEMINI SCENE] "
                    f"video_index={clip.get('video_index')} "
                    f"scene={clip.get('scene_type')} "
                    f"start={clip.get('start')} "
                    f"end={clip.get('end')}"
                )
                
            mapped_timeline = []
            
            for i, c in enumerate(timeline):
                idx = c.get("video_index", 0)
                if idx < len(uploads):
                    logger.info(f"[MAPPING] video_index={idx} mapped_to_upload={uploads[idx].get('_id')}")
                    c["upload_id"] = str(uploads[idx]["_id"])
                    local_path = uploads[idx].get("localPath")
                    c["localPath"] = local_path
                    
                    await q.put({"status": "progress", "message": f"Computer Vision Analysis ({i+1}/{len(timeline)})..."})
                    
                    original_start_sec = parse_time(c.get("start", "0"))
                    original_end_sec = parse_time(c.get("end", "5"))
                    start_sec = original_start_sec
                    end_sec = original_end_sec
                    
                    # V4.0: Lucas-Kanade camera adjustment detection (throttled)
                    async with cv_semaphore:
                        adjustment = await asyncio.to_thread(
                            detect_camera_adjustments, local_path, start_sec, end_sec
                        )
                    
                    if adjustment.get("has_adjustment"):
                        adj_type = adjustment.get("adjustment_type", "unknown")
                        new_start = adjustment.get("trim_start_sec", start_sec)
                        logger.info(f"[CV LK] Clip {i}: Detected {adj_type}. Trimming {start_sec:.1f}s → {new_start:.1f}s")
                        start_sec = new_start
                        c["start"] = str(start_sec)
                        c["camera_adjustment_detected"] = adj_type
                    
                    # Fallback: Dynamic 3s skip if Lucas-Kanade didn't catch it
                    if start_sec < 1.0 and not adjustment.get("has_adjustment"):
                        async with cv_semaphore:
                            first_3s_analysis = await asyncio.to_thread(
                                analyze_video_segment, local_path, 0.0, 3.0
                            )
                        if first_3s_analysis.get("is_unstable"):
                            start_sec = 3.0
                            c["start"] = "3.0"

                    # V2 Stability metadata (safe additive path)
                    v2_should_analyze = (
                        settings.ENABLE_STABILITY_V2
                        or settings.ENABLE_TRIM_V2
                        or settings.PIPELINE_SHADOW_MODE
                    )
                    stability_metrics_v2 = {}
                    tail_stability_score = None
                    if v2_should_analyze:
                        async with cv_semaphore:
                            stability_metrics_v2 = await asyncio.to_thread(
                                analyze_stability_v2, local_path, original_start_sec, original_end_sec
                            )
                        c.update(stability_metrics_v2)

                        tail_start = max(original_start_sec, original_end_sec - 1.2)
                        if original_end_sec - tail_start >= 0.6:
                            async with cv_semaphore:
                                tail_metrics = await asyncio.to_thread(
                                    analyze_stability_v2, local_path, tail_start, original_end_sec
                                )
                            tail_stability_score = tail_metrics.get("stability_score_v2")
                            c["tail_stability_score_v2"] = tail_stability_score

                    trim_recommendation_v2 = recommend_trim_bounds_v2(
                        start_sec=original_start_sec,
                        end_sec=original_end_sec,
                        adjustment_result=adjustment,
                        stability_metrics=stability_metrics_v2,
                        tail_stability_score=tail_stability_score,
                    )
                    c["trim_recommendation_v2"] = trim_recommendation_v2
                    c["v2_trim_applied"] = False

                    # Promote recommendations only when explicitly enabled and confident.
                    if (
                        settings.ENABLE_TRIM_V2
                        and trim_recommendation_v2.get("trim_confidence", 0.0) >= settings.V2_MIN_TRIM_CONFIDENCE
                        and not trim_recommendation_v2.get("fallback_to_original", False)
                    ):
                        rec_start = float(trim_recommendation_v2.get("recommended_trim_start", start_sec))
                        rec_end = float(trim_recommendation_v2.get("recommended_trim_end", end_sec))
                        if rec_end > rec_start:
                            start_sec = rec_start
                            end_sec = rec_end
                            c["start"] = str(start_sec)
                            c["end"] = str(end_sec)
                            c["v2_trim_applied"] = True
                            logger.info(
                                "[TRIM V2] Clip %s trimmed to %.2fs-%.2fs (confidence=%.2f).",
                                c.get("clip_id", i),
                                start_sec,
                                end_sec,
                                trim_recommendation_v2.get("trim_confidence", 0.0),
                            )
                    
                    # Get overall segment CV metrics (throttled)
                    async with cv_semaphore:
                        cv_scores = await asyncio.to_thread(
                            analyze_video_segment, local_path, start_sec, end_sec
                        )
                    c.update(cv_scores)
                    
                    mapped_timeline.append(c)

            # --- MULTI-SEGMENT CAP: Max 3 segments per video ---
            MAX_SEGMENTS_PER_VIDEO = 3
            seg_counts = Counter(c.get("video_index") for c in mapped_timeline)
            over_limit = {vid: count for vid, count in seg_counts.items() if count > MAX_SEGMENTS_PER_VIDEO}
            if over_limit:
                for vid_idx, count in over_limit.items():
                    vid_clips = [(i, c) for i, c in enumerate(mapped_timeline) if c.get("video_index") == vid_idx]
                    vid_clips.sort(key=lambda x: int(x[1].get("hero_score", 0)), reverse=True)
                    remove_indices = [i for i, c in vid_clips[MAX_SEGMENTS_PER_VIDEO:]]
                    for ri in sorted(remove_indices, reverse=True):
                        removed = mapped_timeline.pop(ri)
                        ai_removed.append({"video_index": vid_idx, "reason": f"Multi-segment cap: video {vid_idx} had {count} segments, kept top 3"})
                    logger.info(f"[MULTI-SEGMENT CAP] Video {vid_idx}: had {count} segments, capped to {MAX_SEGMENTS_PER_VIDEO}")

            # --- ASSIGN UNIQUE clip_id ---
            for c in mapped_timeline:
                vid_idx = c.get("video_index", 0)
                start_val = c.get("start", "0")
                end_val = c.get("end", "5")
                c["clip_id"] = f"{vid_idx}_{start_val}_{end_val}"

            # V4.0: Build Property Highlight Memory BEFORE optimization
            await q.put({"status": "progress", "message": "Building Property Highlight Memory..."})
            highlight_memory = build_highlight_memory(mapped_timeline)

            optimized_timeline = TimelineOptimizer.optimize(
                mapped_timeline,
                ai_removed,
                style=style,
                highlight_memory=highlight_memory,
                quality_options=quality_options,
            )
            timeline = optimized_timeline
            
            logger.info(f"[TIMELINE] Final clips: {len(timeline)}")
            for clip in timeline:
                logger.info(
                    f"[FINAL SCENE] "
                    f"video_index={clip.get('video_index')} "
                    f"scene={clip.get('scene_type')}"
                )
                logger.warning(
                    f"[SCENE CHECK] "
                    f"video_index={clip.get('video_index')} "
                    f"scene={clip.get('scene_type')}"
                )

            # Update final_order to match the fixed timeline
            gemini_result["final_order"] = [c.get("video_index") for c in timeline]
            gemini_result["selected_clips"] = timeline
            gemini_result["timeline"] = timeline
            
            # Use 'end' - 'start' to compute duration since clip_duration_sec is gone
            total_sec = sum(float(c.get("clip_duration_sec", 4.0)) for c in timeline)
                
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

            # Debug logging for every removed clip as requested by user
            for dup in all_removed:
                v_id = dup.get("video_index", "-1")
                reason = dup.get("reason", "Unknown reason")
                logger.info(f"REMOVED: Video {v_id} - {reason}")

            # Coverage calculation
            unique_videos_used = len(set(c.get("video_index") for c in timeline if c.get("video_index") is not None))
            coverage_percentage = (unique_videos_used / total_uploaded) * 100 if total_uploaded > 0 else 0
            if unique_videos_used > 0 and coverage_percentage == 0:
                coverage_percentage = 1.0 # Never show 0% if videos were used

            v2_stability_values = [float(c.get("stability_score_v2")) for c in timeline if c.get("stability_score_v2") is not None]
            v2_story_conf_values = [float(c.get("story_classification_confidence")) for c in timeline if c.get("story_classification_confidence") is not None]
            v2_trim_recommendations = sum(1 for c in timeline if c.get("trim_recommendation_v2"))
            v2_trim_applied = sum(1 for c in timeline if c.get("v2_trim_applied"))

            ai_metadata = {
                "analyzed_sec": gemini_result.get("total_analyzed_duration_sec", 0),
                "selected_sec": gemini_result.get("total_selected_duration_sec", 0),
                "duplicates_removed": total_removed,
                "removed_clips": all_removed,
                "quality_v2": {
                    "shadow_mode": settings.PIPELINE_SHADOW_MODE,
                    "flags": {
                        "stability": settings.ENABLE_STABILITY_V2,
                        "trim": settings.ENABLE_TRIM_V2,
                        "story": settings.ENABLE_STORY_V2,
                        "scoring": settings.ENABLE_SCORING_V2,
                        "dedup": settings.ENABLE_DEDUP_V2,
                        "transition": settings.ENABLE_TRANSITION_V2,
                    },
                    "avg_stability_score": round(sum(v2_stability_values) / len(v2_stability_values), 4) if v2_stability_values else None,
                    "avg_story_confidence": round(sum(v2_story_conf_values) / len(v2_story_conf_values), 4) if v2_story_conf_values else None,
                    "trim_recommendations_count": v2_trim_recommendations,
                    "trim_applied_count": v2_trim_applied,
                },
                "coverage_analytics": {
                    "uploaded_count": total_uploaded,
                    "pre_processor_duplicates": len(pre_duplicates),
                    "ai_duplicates": len(ai_removed),
                    "duplicates_removed": total_removed,
                    "selected_count": len(timeline),
                    "unique_videos_used": unique_videos_used,
                    "coverage_percentage": round(coverage_percentage, 2)
                }
            }
            await db.projects.update_one(
                {"_id": project_oid},
                {"$set": {
                    "draftTimeline": timeline, 
                    "status": "ANALYZED",
                    "aiMetadata": ai_metadata
                }}
            )
            await invalidate_after_project_mutation(user["_id"], project_id)

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
    project_oid = parse_object_id(project_id, "project_id")
    
    project = await db.projects.find_one({"_id": project_oid, "userId": user["_id"]})
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

            # Phase 5: RENDER COVERAGE AUDIT setup
            # Populate localPath directly into the timeline blocks
            import urllib.parse
            for item in timeline:
                upload_id = item.get("upload_id")
                if upload_id and not item.get("localPath"):
                    if not ObjectId.is_valid(upload_id):
                        logger.warning(f"Skipping invalid upload_id in timeline: {upload_id}")
                        continue
                    upload = await db.uploads.find_one({"_id": parse_object_id(upload_id, "upload_id")})
                    if upload and upload.get("localPath"):
                        item["localPath"] = upload["localPath"]
                        
                # Ensure legacy paths with %20 are unquoted to match the new on-disk filenames
                if item.get("localPath") and "%" in item.get("localPath"):
                    item["localPath"] = urllib.parse.unquote(item["localPath"])

            target_duration = _parse_target_duration(duration)

            results = []

            for i, var in enumerate(variations):
                var_style = var.get("style", style)
                await q.put({"status": "progress", "message": f"Rendering {var_style} variation ({i+1}/{len(variations)})..."})
                
                # Build custom timeline using clip_id (strings, not integers)
                custom_seq = var.get("custom_sequence", [])
                timeline_map = {block.get("clip_id", f"{block.get('video_index')}_{block.get('start','0')}_{block.get('end','5')}"): block for block in timeline}
                
                # Start with clips in custom_sequence order
                var_timeline = []
                used_ids = set()
                for cid in custom_seq:
                    cid_str = str(cid)  # Ensure string comparison
                    if cid_str in timeline_map and cid_str not in used_ids:
                        var_timeline.append(timeline_map[cid_str])
                        used_ids.add(cid_str)
                
                # CRITICAL: Append ALL missing clips in original timeline order
                # This ensures NO clips are ever removed by the variation generator
                for block in timeline:
                    block_id = block.get("clip_id", f"{block.get('video_index')}_{block.get('start','0')}_{block.get('end','5')}")
                    if block_id not in used_ids:
                        var_timeline.append(block)
                        used_ids.add(block_id)
                
                logger.info(f"[VARIATION {var_style}] custom_seq had {len(custom_seq)} clips, var_timeline has {len(var_timeline)} clips (timeline has {len(timeline)})")
                
                # Safety: if somehow var_timeline is still empty, use original
                if not var_timeline:
                    var_timeline = timeline

                # Render video for this variation
                result = await build_reel(
                    timeline_blocks=var_timeline,
                    property_name=project["title"],
                    target_duration_sec=target_duration,
                    style=var_style,
                    project_id=project_id,
                    aspect_ratio=aspect_ratio,
                    music_path=music_path,
                    music_volume=music_volume,
                    vo_volume=vo_volume
                )
                
                # Extract render audit data from build_reel dict
                if isinstance(result, dict):
                    output_path = result.get("output_path", "")
                    rendered_count = result.get("rendered_count", len(var_timeline))
                    selected_count = result.get("selected_count", len(var_timeline))
                    selected_duration_sec = result.get("selected_duration_sec", 0)
                    rendered_duration_sec = result.get("rendered_duration_sec", 0)
                    duration_coverage_pct = result.get("duration_coverage_pct", 100)
                    skipped_clips = result.get("skipped_clips", [])
                elif isinstance(result, tuple) and len(result) >= 2:
                    output_path = result[0]
                    rendered_count = result[1]
                    selected_count = len(var_timeline)
                    selected_duration_sec = sum(float(c.get("clip_duration_sec", 4.0)) for c in var_timeline)
                    rendered_duration_sec = 0
                    duration_coverage_pct = 100
                    skipped_clips = []
                else:
                    output_path = str(result)
                    rendered_count = len(var_timeline)
                    selected_count = len(var_timeline)
                    selected_duration_sec = sum(float(c.get("clip_duration_sec", 4.0)) for c in var_timeline)
                    rendered_duration_sec = 0
                    duration_coverage_pct = 100
                    skipped_clips = []
                    
                logger.info(f"[RENDERED_COUNT] {rendered_count}")
                logger.info(f"[OUTPUT_PATH] {output_path}")
                
                # --- V4.0 FAULT-TOLERANT RENDER AUDIT GATE ---
                render_success_pct = (rendered_count / selected_count * 100) if selected_count > 0 else 100
                
                if render_success_pct >= 95:
                    audit_status = "PASS"
                    logger.info(f"[RENDER AUDIT] PASS: {var_style} ({render_success_pct:.1f}%). "
                                f"Selected {selected_count}, Rendered {rendered_count}.")
                elif render_success_pct >= 90:
                    audit_status = "WARNING"
                    missing_clips = selected_count - rendered_count
                    logger.warning(f"[RENDER AUDIT] WARNING: {var_style} ({render_success_pct:.1f}%). "
                                   f"Selected {selected_count}, Rendered {rendered_count}. "
                                   f"Missing {missing_clips} clips — logging and delivering.")
                    await q.put({"status": "progress", "message": f"Render audit WARNING: {render_success_pct:.1f}% success ({missing_clips} clips dropped)"})
                else:
                    audit_status = "FAIL"
                    missing_clips = selected_count - rendered_count
                    logger.error(f"[RENDER AUDIT] FAIL: {var_style} ({render_success_pct:.1f}%). "
                                 f"Selected {selected_count}, Rendered {rendered_count}. "
                                 f"Missing {missing_clips} clips — HALTING DELIVERY.")
                    await q.put({"status": "progress", "message": f"Render audit FAIL: only {render_success_pct:.1f}% success. Halting delivery for reprocessing."})
                    # FAIL: Skip this variation — do not deliver
                    continue

                web_url = "/" + output_path.replace("\\", "/")
                
                # Use rendered_duration from build_reel if available
                if rendered_duration_sec > 0:
                    actual_duration_str = f"{int(rendered_duration_sec)}s"
                else:
                    try:
                        from services.video import get_exact_duration
                        actual_dur_sec = await asyncio.to_thread(get_exact_duration, output_path)
                        actual_duration_str = f"{int(actual_dur_sec)}s"
                        rendered_duration_sec = actual_dur_sec
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
                insert_result = await db.generated_shorts.insert_one(short)
                
                short["_id"] = str(insert_result.inserted_id)
                short["projectId"] = str(short["projectId"])
                short["userId"] = str(short["userId"])
                
                results.append(short)

                # Update project with full render audit
                render_audit_data = {
                    "selected_count": selected_count,
                    "rendered_count": rendered_count,
                    "selected_duration": round(selected_duration_sec, 1),
                    "rendered_duration": round(rendered_duration_sec, 1),
                    "duration_coverage": round(duration_coverage_pct, 1),
                    "render_success_percentage": round(render_success_pct, 2),
                    "audit_status": audit_status,
                    "coverage": round((rendered_count / selected_count * 100) if selected_count > 0 else 100, 1),
                    "skipped_clips": skipped_clips
                }
                
                await db.projects.update_one(
                    {"_id": project_oid},
                    {
                        "$set": {
                            "status": "COMPLETED",
                            f"aiMetadata.render_audit.{var_style}": render_audit_data
                        }, 
                        "$inc": {"generatedCount": 1}
                    }
                )

            if results:
                await invalidate_after_generation_mutation(user["_id"], project_id)
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
