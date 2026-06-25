import os
import signal
import asyncio
import sys
import logging
from contextlib import asynccontextmanager

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
from app.core.http_client import connect_http_client, close_http_client
from app.core.cache import cache_get, cache_set, connect_cache, close_cache
from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.core.rate_limit import RateLimitMiddleware
from app.core.request_context import RequestContextMiddleware
from app.core.runtime_health import (
    mark_background_task_crash,
    mark_background_task_running,
    mark_background_task_stopped,
    mark_component_status,
)
from app.core.alerts import send_alert
from app.core.tracing import setup_tracing
from app.core.metrics import setup_metrics
from app.core.worker import process_pending_uploads
from app.api import auth
from app.api import projects as projects_api
from app.api import uploads as uploads_api
from app.api import generation as generation_api
from app.api import history as history_api
from app.api import health as health_api

load_dotenv()
settings = get_settings()
configure_logging(settings)
try:
    import structlog  # type: ignore
except Exception:
    structlog = None
logger = structlog.get_logger(__name__) if structlog is not None else logging.getLogger(__name__)

from app.core.cleanup import run_daily_cleanup

async def connect_with_retry(component_name, connector):
    attempts = max(1, settings.STARTUP_RETRY_ATTEMPTS)
    base_delay = max(1, settings.STARTUP_RETRY_BASE_DELAY_SEC)
    max_delay = max(base_delay, settings.STARTUP_RETRY_MAX_DELAY_SEC)

    for attempt in range(1, attempts + 1):
        try:
            await connector()
            mark_component_status(component_name, True)
            return
        except Exception as exc:
            mark_component_status(component_name, False, str(exc))
            logger.error(
                "[STARTUP] Component init failed component=%s attempt=%s/%s error=%s",
                component_name,
                attempt,
                attempts,
                exc,
            )
            if attempt >= attempts:
                await send_alert(
                    event="startup_component_failed",
                    message=f"{component_name} failed during startup after {attempts} attempts.",
                    severity="critical",
                    details={"component": component_name, "error": str(exc), "attempts": attempts},
                    alert_key=f"startup:{component_name}",
                )
                raise
            delay = min(max_delay, base_delay * attempt)
            await asyncio.sleep(delay)


async def safe_background_task(coro_func, name):
    """Wrap background tasks so crashes restart instead of killing the server."""
    consecutive_failures = 0
    while True:
        try:
            mark_background_task_running(name)
            logger.info(f"[CRASH GUARD] Starting background task: {name}")
            await coro_func()
            consecutive_failures = 0
            logger.warning(f"[CRASH GUARD] Background task '{name}' exited unexpectedly. Restarting in 1s...")
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            mark_background_task_stopped(name)
            logger.info("[CRASH GUARD] Background task '%s' cancelled.", name)
            raise
        except Exception as e:
            consecutive_failures = mark_background_task_crash(name, e)
            delay = min(60, 5 * max(1, consecutive_failures))
            logger.error(f"[CRASH GUARD] Background task '{name}' crashed: {e}")
            logger.error(f"[CRASH GUARD] Restarting '{name}' in {delay}s...")
            if consecutive_failures >= settings.ALERT_MIN_CONSECUTIVE_BACKGROUND_FAILURES:
                await send_alert(
                    event="background_task_crash",
                    message=f"Background task '{name}' crashed repeatedly.",
                    severity="critical",
                    details={
                        "task": name,
                        "error": str(e),
                        "consecutive_failures": consecutive_failures,
                        "retry_delay_sec": delay,
                    },
                    alert_key=f"task:{name}",
                )
            await asyncio.sleep(delay)

@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_with_retry("mongo", connect_to_mongo)
    await connect_with_retry("http_client", connect_http_client)
    await connect_with_retry("cache", connect_cache)

    # Start background workers with crash protection
    upload_task = asyncio.create_task(safe_background_task(process_pending_uploads, "upload_worker"))
    cleanup_task = asyncio.create_task(safe_background_task(run_daily_cleanup, "daily_cleanup"))
    tasks = (upload_task, cleanup_task)
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

        await close_cache()
        mark_component_status("cache", False)

        await close_http_client()
        mark_component_status("http_client", False)

        await close_mongo_connection()
        mark_component_status("mongo", False)

app = FastAPI(lifespan=lifespan)
setup_tracing(app, settings)
setup_metrics(app, settings)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(RateLimitMiddleware)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(projects_api.router, prefix="/api/v1")
app.include_router(uploads_api.router, prefix="/api/v1")
app.include_router(generation_api.router, prefix="/api/v1")
app.include_router(history_api.router, prefix="/api/v1")
app.include_router(health_api.router, prefix="/api/v1")

@app.get("/api/v1/music-library")
async def get_music_library():
    """Dynamically scan and return music from the user's library folder."""
    cache_key = "rf:cache:music-library:v1"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

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
    response = {"library": tracks}
    await cache_set(cache_key, response, settings.CACHE_TTL_MUSIC_LIBRARY_SEC)
    return response

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
    if os.path.exists("static/demo"):
        app.mount("/demo", StaticFiles(directory="static/demo"), name="demo")
    if os.path.exists("static/tutorials"):
        app.mount("/tutorials", StaticFiles(directory="static/tutorials"), name="tutorials")

if os.path.exists("static/index.html"):
    @app.get("/")
    async def root():
        return FileResponse("static/index.html")

    @app.get("/favicon.svg")
    async def favicon():
        if os.path.exists("static/favicon.svg"):
            return FileResponse("static/favicon.svg")
        return JSONResponse({"error": "Favicon not found"}, status_code=404)

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        # Keep API/static mount 404 behavior; only fallback frontend routes to index.html
        if full_path.startswith(("api/", "outputs/", "data/", "assets/", "demo/", "tutorials/")):
            return JSONResponse({"detail": "Not Found"}, status_code=404)

        static_candidate = os.path.join("static", full_path)
        if full_path and os.path.isfile(static_candidate):
            return FileResponse(static_candidate)

        return FileResponse("static/index.html")
