import os
import json
import asyncio
import sys
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from services.video import download_video, create_preview, process_segments_parallel
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
async def process_video(video_url: str, property_name: str, request: Request):
    q = asyncio.Queue()

    async def background_task():
        job_start = time.perf_counter()
        try:
            await q.put({"status": "progress", "message": "Starting process..."})

            # ── Step 1: Download video ──────────────────────────
            await q.put({"status": "progress", "message": "Downloading video from Dropbox..."})
            local_input_path = os.path.join("downloads", "input_video.mp4")
            await download_video(video_url, local_input_path)

            # ── Step 2: Create 480p preview for Gemini ──────────
            await q.put({"status": "progress", "message": "Creating low-res preview for AI analysis..."})
            preview_path = os.path.join("downloads", "preview_480p.mp4")
            
            if not os.path.exists(local_input_path):
                raise RuntimeError("Video file missing before FFmpeg stage")
                
            await create_preview(local_input_path, preview_path)

            # ── Step 3: Upload preview to Gemini & wait ─────────
            async def yield_message(msg: str):
                await q.put({"status": "progress", "message": msg})

            file_info = await upload_and_wait(preview_path, property_name, yield_callback=yield_message)

            # ── Step 4: Single Gemini call — analysis + scripts ─
            await q.put({"status": "progress", "message": "AI analyzing video & generating scripts..."})
            segments = await analyze_and_generate(file_info.uri, property_name)

            # ── Step 5: Parallel FFmpeg export ──────────────────
            await q.put({"status": "progress", "message": f"Exporting {len(segments)} clips in parallel..."})
            results = await process_segments_parallel(local_input_path, segments, "outputs")

            # ── Done ────────────────────────────────────────────
            total_elapsed = time.perf_counter() - job_start
            print(f"[PERF] ═══ TOTAL JOB: {total_elapsed:.1f}s ═══")

            await q.put({"status": "completed", "results": results})

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
