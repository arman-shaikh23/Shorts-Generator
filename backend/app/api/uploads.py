from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import os
import re
import uuid
import aiofiles
from pathlib import Path
import urllib.parse
from ..core.cache import (
    build_uploads_cache_key,
    cache_get,
    cache_set,
    invalidate_after_upload_mutation,
)
from ..core.config import get_settings
from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..core.mongo_utils import parse_object_id
from ..core.pagination import build_pagination_meta, normalize_limit, resolve_page_skip
import datetime

router = APIRouter(prefix="/projects/{project_id}/uploads", tags=["Uploads"])

# ── Request Models ──────────────────────────────────────

class AddUrlsRequest(BaseModel):
    urls: List[str]

class ReorderRequest(BaseModel):
    upload_ids: List[str]  # ordered list of upload IDs

# ── Helpers ─────────────────────────────────────────────

async def verify_project_ownership(project_id: str, user: dict):
    db = get_db()
    project_oid = parse_object_id(project_id, "project_id")
    project = await db.projects.find_one({"_id": project_oid, "userId": user["_id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def sanitize_filename(filename: str, fallback_ext: str = ".bin") -> str:
    raw_name = urllib.parse.unquote(filename or "")
    base_name = Path(raw_name).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", base_name).strip("._")
    if cleaned:
        return cleaned
    return f"upload_{uuid.uuid4().hex}{fallback_ext}"


def _remove_file_if_exists(path: str) -> None:
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


async def stream_upload_to_disk(
    file: UploadFile,
    destination_path: str,
    *,
    max_bytes: int,
    chunk_size: int,
) -> int:
    total_bytes = 0
    max_megabytes = max(1, max_bytes // (1024 * 1024))

    try:
        async with aiofiles.open(destination_path, "wb") as output_file:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break

                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum allowed size is {max_megabytes} MB.",
                    )
                await output_file.write(chunk)
    except HTTPException:
        _remove_file_if_exists(destination_path)
        raise
    except Exception:
        _remove_file_if_exists(destination_path)
        raise
    finally:
        await file.close()

    if total_bytes == 0:
        _remove_file_if_exists(destination_path)
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    return total_bytes

# ── Endpoints ───────────────────────────────────────────

@router.post("")
async def add_uploads(project_id: str, req: AddUrlsRequest, user=Depends(get_current_user)):
    """Add video URLs to a project. Creates upload records with PENDING status."""
    await verify_project_ownership(project_id, user)
    db = get_db()
    project_oid = parse_object_id(project_id, "project_id")
    now = datetime.datetime.utcnow()

    # Get current max order
    last = await db.uploads.find_one(
        {"projectId": project_id},
        sort=[("order", -1)]
    )
    start_order = (last["order"] + 1) if last else 0

    created = []
    for i, url in enumerate(req.urls):
        upload = {
            "projectId": project_id,
            "userId": user["_id"],
            "originalUrl": url,
            "localPath": None,
            "previewPath": None,
            "thumbnailPath": None,
            "filename": url.split("/")[-1].split("?")[0] or f"video_{start_order + i}.mp4",
            "fileSize": None,
            "duration": None,
            "status": "PENDING",
            "roomType": None,
            "qualityScore": None,
            "order": start_order + i,
            "uploadedAt": now,
        }
        result = await db.uploads.insert_one(upload)
        upload["_id"] = str(result.inserted_id)
        created.append(upload)

    # Update project upload count and timestamp
    count = await db.uploads.count_documents({"projectId": project_id})
    await db.projects.update_one(
        {"_id": project_oid},
        {"$set": {"uploadCount": count, "updatedAt": now}}
    )
    await invalidate_after_upload_mutation(user["_id"], project_id)

    return {"uploads": created, "total": count}

@router.post("/file")
async def upload_local_file(project_id: str, file: UploadFile = File(...), user=Depends(get_current_user)):
    """Handle raw video file uploads directly."""
    await verify_project_ownership(project_id, user)
    db = get_db()
    project_oid = parse_object_id(project_id, "project_id")
    settings = get_settings()
    now = datetime.datetime.utcnow()

    # 1. Save File Locally
    extension = Path(file.filename or "").suffix or ".mp4"
    clean_filename = sanitize_filename(file.filename or "", fallback_ext=extension)
    project_dir = f"data/{project_id}/downloads"
    os.makedirs(project_dir, exist_ok=True)
    local_path = os.path.join(project_dir, clean_filename)
    
    file_size = await stream_upload_to_disk(
        file,
        local_path,
        max_bytes=settings.MAX_VIDEO_UPLOAD_BYTES,
        chunk_size=settings.UPLOAD_STREAM_CHUNK_SIZE,
    )

    # 2. Get order
    last = await db.uploads.find_one(
        {"projectId": project_id},
        sort=[("order", -1)]
    )
    start_order = (last["order"] + 1) if last else 0

    # 3. Create Upload Record (mark as PROCESSING initially)
    upload = {
        "projectId": project_id,
        "userId": user["_id"],
        "originalUrl": f"local://{clean_filename}",
        "localPath": local_path,
        "previewPath": None,
        "thumbnailPath": None,
        "filename": clean_filename,
        "fileSize": file_size,
        "duration": None,
        "status": "PENDING", # Let the worker handle the preview generation! We just need to modify worker to skip download if localPath exists!
        "roomType": None,
        "qualityScore": None,
        "order": start_order,
        "uploadedAt": now,
    }
    result = await db.uploads.insert_one(upload)
    upload["_id"] = str(result.inserted_id)

    # Update project upload count
    count = await db.uploads.count_documents({"projectId": project_id})
    await db.projects.update_one(
        {"_id": project_oid},
        {"$set": {"uploadCount": count, "updatedAt": now}}
    )
    await invalidate_after_upload_mutation(user["_id"], project_id)

    return {"uploads": [upload], "total": count}


@router.post("/music")
async def upload_custom_music(project_id: str, file: UploadFile = File(...), user=Depends(get_current_user)):
    """Handle custom music uploads (.mp3, .wav, .m4a)."""
    await verify_project_ownership(project_id, user)
    settings = get_settings()
    ext = Path(file.filename or "").suffix.lower()
    if ext not in {".mp3", ".wav", ".m4a"}:
        raise HTTPException(status_code=400, detail="Unsupported audio format")
    
    # 1. Save File Locally
    music_dir = f"data/{project_id}/music"
    os.makedirs(music_dir, exist_ok=True)
    safe_name = sanitize_filename(file.filename or "", fallback_ext=ext or ".mp3")
    local_path = os.path.join(music_dir, safe_name)
    
    await stream_upload_to_disk(
        file,
        local_path,
        max_bytes=settings.MAX_MUSIC_UPLOAD_BYTES,
        chunk_size=settings.UPLOAD_STREAM_CHUNK_SIZE,
    )
        
    return {"message": "Music uploaded successfully", "localPath": local_path, "filename": safe_name}

@router.get("")
async def list_uploads(
    project_id: str,
    user=Depends(get_current_user),
    page: Optional[int] = None,
    skip: Optional[int] = None,
    limit: Optional[int] = None,
    paginate: bool = False,
):
    """List all uploads for a project, sorted by order."""
    await verify_project_ownership(project_id, user)
    db = get_db()
    settings = get_settings()

    should_paginate = paginate or page is not None or skip is not None or limit is not None
    uploads = []

    if should_paginate:
        safe_limit = normalize_limit(limit, default_limit=20, max_limit=100)
        safe_page, safe_skip = resolve_page_skip(page=page, skip=skip, limit=safe_limit)
        cache_key = await build_uploads_cache_key(
            project_id,
            mode="paged",
            page=safe_page,
            limit=safe_limit,
            skip=safe_skip,
        )
        cached = await cache_get(cache_key)
        if cached is not None:
            return cached

        total = await db.uploads.count_documents({"projectId": project_id})
        cursor = (
            db.uploads.find({"projectId": project_id})
            .sort("order", 1)
            .skip(safe_skip)
            .limit(safe_limit)
        )
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            uploads.append(doc)

        pagination = build_pagination_meta(total=total, page=safe_page, limit=safe_limit, skip=safe_skip)
        response = {"uploads": uploads, **pagination}
        await cache_set(cache_key, response, settings.CACHE_TTL_UPLOADS_SEC)
        return response

    cache_key = await build_uploads_cache_key(project_id, mode="all", page=1, limit=1, skip=0)
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    cursor = db.uploads.find({"projectId": project_id}).sort("order", 1)
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        uploads.append(doc)

    total = len(uploads)
    pagination = build_pagination_meta(total=total, page=1, limit=max(1, total or 1), skip=0)
    response = {"uploads": uploads, **pagination}
    await cache_set(cache_key, response, settings.CACHE_TTL_UPLOADS_SEC)
    return response


@router.delete("/{upload_id}")
async def delete_upload(project_id: str, upload_id: str, user=Depends(get_current_user)):
    """Remove a single upload from the project."""
    await verify_project_ownership(project_id, user)
    db = get_db()

    upload_oid = parse_object_id(upload_id, "upload_id")
    upload = await db.uploads.find_one({"_id": upload_oid, "projectId": project_id})
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    await db.uploads.delete_one({"_id": upload_oid})

    # Update project count
    count = await db.uploads.count_documents({"projectId": project_id})
    await db.projects.update_one(
        {"_id": parse_object_id(project_id, "project_id")},
        {"$set": {"uploadCount": count, "updatedAt": datetime.datetime.utcnow()}}
    )
    await invalidate_after_upload_mutation(user["_id"], project_id)

    return {"message": "Upload deleted", "total": count}


@router.patch("/reorder")
async def reorder_uploads(project_id: str, req: ReorderRequest, user=Depends(get_current_user)):
    """Reorder uploads by providing an ordered list of upload IDs."""
    await verify_project_ownership(project_id, user)
    db = get_db()

    for i, uid in enumerate(req.upload_ids):
        upload_oid = parse_object_id(uid, "upload_id")
        await db.uploads.update_one(
            {"_id": upload_oid, "projectId": project_id},
            {"$set": {"order": i}}
        )

    await invalidate_after_upload_mutation(user["_id"], project_id)
    return {"message": "Reordered", "order": req.upload_ids}
