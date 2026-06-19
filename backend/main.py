import os
import signal
import asyncio
import sys
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

def force_exit(*args):
    print("\n[SHUTDOWN] Forcefully exiting to bypass hanging Gemini threads...")
    os._exit(0)

# Ensure Ctrl+C immediately terminates backend
signal.signal(signal.SIGINT, force_exit)

from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.worker import process_pending_uploads
from app.api import auth
from app.api import projects as projects_api
from app.api import uploads as uploads_api
from app.api import generation as generation_api
from app.api import history as history_api

load_dotenv()

from app.core.cleanup import run_daily_cleanup

async def safe_background_task(coro_func, name):
    """Wrap background tasks so crashes restart instead of killing the server."""
    while True:
        try:
            logger.info(f"[CRASH GUARD] Starting background task: {name}")
            await coro_func()
        except Exception as e:
            logger.error(f"[CRASH GUARD] Background task '{name}' crashed: {e}")
            logger.error(f"[CRASH GUARD] Restarting '{name}' in 10s...")
            await asyncio.sleep(10)

@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_to_mongo()
    # Start background workers with crash protection
    upload_task = asyncio.create_task(safe_background_task(process_pending_uploads, "upload_worker"))
    cleanup_task = asyncio.create_task(safe_background_task(run_daily_cleanup, "daily_cleanup"))
    try:
        yield
    finally:
        for task in (upload_task, cleanup_task):
            task.cancel()
        await close_mongo_connection()

app = FastAPI(lifespan=lifespan)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(projects_api.router, prefix="/api/v1")
app.include_router(uploads_api.router, prefix="/api/v1")
app.include_router(generation_api.router, prefix="/api/v1")
app.include_router(history_api.router, prefix="/api/v1")

@app.get("/api/v1/music-library")
async def get_music_library():
    """Dynamically scan and return music from the user's library folder."""
    library_dir = "data/library/music"
    os.makedirs(library_dir, exist_ok=True)
    tracks = []
    for f in os.listdir(library_dir):
        if f.lower().endswith(('.mp3', '.wav', '.m4a')):
            # Guess tag from filename, or default to Custom
            tag = "Custom"
            name = f.rsplit('.', 1)[0].replace('_', ' ').title()
            if "lux" in f.lower(): tag = "Luxury"
            elif "cine" in f.lower(): tag = "Cinematic"
            elif "viral" in f.lower(): tag = "Viral"
            elif "real" in f.lower(): tag = "Realtor"
            elif "ambient" in f.lower(): tag = "Ambient"
            
            tracks.append({
                "name": name,
                "path": f"{library_dir}/{f}",
                "tag": tag
            })
    return {"library": tracks}

allowed_origins_env = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
if not allowed_origins:
    allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

allow_credentials = "*" not in allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("downloads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)
os.makedirs("data", exist_ok=True)

app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
app.mount("/data", StaticFiles(directory="data"), name="data")

# Serve frontend build if it exists
if os.path.exists("static"):
    if os.path.exists("static/assets"):
        app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")

if os.path.exists("static/index.html"):
    @app.get("/")
    async def root():
        return FileResponse("static/index.html")

    @app.get("/favicon.svg")
    async def favicon():
        if os.path.exists("static/favicon.svg"):
            return FileResponse("static/favicon.svg")
        return JSONResponse({"error": "Favicon not found"}, status_code=404)
