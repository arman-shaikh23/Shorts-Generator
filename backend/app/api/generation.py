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
            # 1. Fetch all PROCESSED uploads
            cursor = db.uploads.find({"projectId": project_id, "status": "PROCESSED"}).sort("order", 1)
            uploads = []
            async for doc in cursor:
                uploads.append(doc)

            if len(uploads) < 3:
                await q.put({"status": "error", "message": f"Need at least 3 processed clips. Found {len(uploads)}."})
                return

            await q.put({"status": "progress", "message": f"Found {len(uploads)} processed clips. Uploading to AI..."})

            # 2. Upload previews to Gemini
            upload_tasks = []
            for i, up in enumerate(uploads):
                if not up.get("previewPath"):
                    continue
                upload_tasks.append(upload_and_wait(up["previewPath"], f"{project['title']}_part{i}"))

            file_infos = await asyncio.gather(*upload_tasks)
            file_uris = [info.uri for info in file_infos]

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

            gemini_result = await analyze_and_generate(file_uris, project["title"], duration, style, yield_callback=yield_message)

            # Map the Gemini result to the actual upload objects
            # Assuming Gemini returns final_order referencing the original index
            timeline = []
            if "final_order" in gemini_result and "selected_clips" in gemini_result:
                clips_map = {c["video_index"]: c for c in gemini_result["selected_clips"]}
                for idx in gemini_result["final_order"]:
                    if idx in clips_map:
                        clip_data = clips_map[idx]
                        if idx < len(uploads):
                            clip_data["upload_id"] = str(uploads[idx]["_id"])
                            clip_data["localPath"] = uploads[idx].get("localPath")
                        timeline.append(clip_data)
            else:
                timeline = gemini_result.get("selected_clips", [])
                for c in timeline:
                    idx = c.get("video_index", 0)
                    if idx < len(uploads):
                        c["upload_id"] = str(uploads[idx]["_id"])
                        c["localPath"] = uploads[idx].get("localPath")

            gemini_result["timeline"] = timeline

            # Save the timeline and AI metadata to the project
            ai_metadata = {
                "analyzed_sec": gemini_result.get("total_analyzed_duration_sec", 0),
                "selected_sec": gemini_result.get("total_selected_duration_sec", 0),
                "duplicates_removed": gemini_result.get("duplicates_removed_count", 0)
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

            target_duration = 30
            if "20" in duration: target_duration = 20
            elif "45" in duration: target_duration = 45

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
                    aspect_ratio=aspect_ratio
                )

                web_url = "/" + output_path.replace("\\", "/")

                # Save to generated shorts
                short = {
                    "projectId": project_id,
                    "userId": user["_id"],
                    "videoUrl": web_url,
                    "duration": duration,
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
