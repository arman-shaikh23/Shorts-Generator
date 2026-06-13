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

from services.video import download_video, create_preview, build_reel, get_total_duration
from services.gemini import upload_and_wait, analyze_and_generate

from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.worker import process_pending_uploads
from app.api import auth
from app.api import projects as projects_api
from app.api import uploads as uploads_api
from app.api import generation as generation_api
from app.api import history as history_api

load_dotenv()

app = FastAPI()

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()
    # Start the background worker
    asyncio.create_task(process_pending_uploads())

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

app.include_router(auth.router, prefix="/api/v1")
app.include_router(projects_api.router, prefix="/api/v1")
app.include_router(uploads_api.router, prefix="/api/v1")
app.include_router(generation_api.router, prefix="/api/v1")
app.include_router(history_api.router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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

    @app.get("/")
    async def root():
        return FileResponse("static/index.html")

    @app.get("/favicon.svg")
    async def favicon():
        if os.path.exists("static/favicon.svg"):
            return FileResponse("static/favicon.svg")
        return JSONResponse({"error": "Favicon not found"}, status_code=404)
