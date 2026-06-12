import os
import json
import asyncio
import sys
import time
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from services.video import download_video, create_preview, build_reel
from services.gemini import upload_and_wait, analyze_and_generate

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("downloads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# Serve frontend build if it exists
if os.path.exists("static"):
    if os.path.exists("static/assets"):
        app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")

    @app.get("/")
    async def root():
        return FileResponse("static/index.html")

    @app.get("/favicon.svg")
    async def favicon():
        if os.path.exists("static/favicon.svg"):
            return FileResponse("static/favicon.svg")
        return JSONResponse({"error": "Favicon not found"}, status_code=404)

@app.get("/api/process")
async def process_video(property_name: str, request: Request, video_url: list[str] = Query(default=[])):
    q = asyncio.Queue()

    async def background_task():
        job_start = time.perf_counter()
        try:
            if not (5 <= len(video_url) <= 10):
                raise ValueError(f"Must provide between 5 and 10 video URLs. You provided {len(video_url)}.")
                
            await q.put({"status": "progress", "message": f"Starting process for {len(video_url)} videos..."})

            local_inputs = []
            preview_paths = []

            # ── Step 1: Download & Preview ──────────────────────────
            for i, url in enumerate(video_url):
                await q.put({"status": "progress", "message": f"Downloading & previewing video {i+1}/{len(video_url)}..."})
                
                local_input = os.path.join("downloads", f"input_video_{i}.mp4")
                preview_path = os.path.join("downloads", f"preview_480p_{i}.mp4")
                
                await download_video(url, local_input)
                
                if not os.path.exists(local_input):
                    raise RuntimeError(f"Video file missing before FFmpeg stage: {local_input}")
                    
                await create_preview(local_input, preview_path)
                
                local_inputs.append(local_input)
                preview_paths.append(preview_path)

            # ── Step 2: Upload previews to Gemini ────────────────
            await q.put({"status": "progress", "message": "Uploading all previews to AI..."})
            
            upload_tasks = []
            for i, p_path in enumerate(preview_paths):
                upload_tasks.append(upload_and_wait(p_path, f"{property_name}_part{i}"))
                
            file_infos = await asyncio.gather(*upload_tasks)
            file_uris = [info.uri for info in file_infos]

            # ── Step 3: Single Gemini call ───────────────────────
            await q.put({"status": "progress", "message": "AI analyzing all videos to build the ultimate reel..."})
            gemini_result = await analyze_and_generate(file_uris, property_name)
            gemini_result["selected_scenes"] = gemini_result.get("timeline", [])

            # ── Step 4: Build single reel ───────────────────────
            await q.put({"status": "progress", "message": "Assembling the final reel..."})
            
            final_reel_url = await build_reel(local_inputs, gemini_result["timeline"], "outputs")
            gemini_result["video_url"] = final_reel_url

            # ── Done ────────────────────────────────────────────
            total_elapsed = time.perf_counter() - job_start
            print(f"[PERF] ═══ TOTAL JOB: {total_elapsed:.1f}s ═══")

            await q.put({"status": "completed", "results": [gemini_result]})

        except Exception as e:
            import traceback
            traceback.print_exc()
            total_elapsed = time.perf_counter() - job_start
            print(f"[PERF] ═══ JOB FAILED after {total_elapsed:.1f}s ═══")
            print(f"[ERROR] Exception type: {type(e).__name__}, Message: {str(e)}")
            await q.put({
                "status": "error",
                "message": str(e),
                "type": type(e).__name__
            })

    # Start the background task
    task = asyncio.create_task(background_task())

    async def event_generator():
        while True:
            if await request.is_disconnected():
                task.cancel()
                break

            msg = await q.get()
            yield {"data": json.dumps(msg)}
            if msg.get("status") in ["completed", "error"]:
                break

    return EventSourceResponse(event_generator())
