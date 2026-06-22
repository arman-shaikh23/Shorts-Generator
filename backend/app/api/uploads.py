from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import os
import re
import json
import uuid
import aiofiles
import subprocess
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
from ..core.idempotency import (
    begin_idempotent_operation,
    complete_idempotent_operation,
    fail_idempotent_operation,
)
from ..core.mongo_utils import parse_object_id
from ..core.pagination import build_pagination_meta, normalize_limit, resolve_page_skip
import datetime

router = APIRouter(prefix="/projects/{project_id}/uploads", tags=["Uploads"])

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif"}
ALLOWED_MEDIA_EXTENSIONS = ALLOWED_VIDEO_EXTENSIONS | ALLOWED_IMAGE_EXTENSIONS

ALLOWED_VIDEO_CONTENT_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-matroska",
    "video/x-msvideo",
    "video/webm",
    "application/octet-stream",
}
ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/bmp",
    "image/tiff",
    "image/gif",
}
ALLOWED_MEDIA_CONTENT_TYPES = ALLOWED_VIDEO_CONTENT_TYPES | ALLOWED_IMAGE_CONTENT_TYPES

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


def _is_youtube_host(host: str) -> bool:
    h = (host or "").lower().split(":")[0]
    if h in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"}:
        return True
    return h.endswith(".youtube.com")


def _validate_remote_url(url: str) -> urllib.parse.ParseResult:
    parsed = urllib.parse.urlparse((url or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(
            status_code=422,
            detail="Invalid URL. Please provide a full http(s) link.",
        )
    return parsed


def _extract_youtube_video_id(parsed: urllib.parse.ParseResult) -> str:
    host = (parsed.netloc or "").lower().split(":")[0]
    if host == "youtu.be":
        return (parsed.path or "").strip("/").split("/")[0]

    params = urllib.parse.parse_qs(parsed.query or "")
    if params.get("v"):
        return params["v"][0]

    path_parts = [p for p in (parsed.path or "").split("/") if p]
    if len(path_parts) >= 2 and path_parts[0] in {"shorts", "live"}:
        return path_parts[1]
    return ""


def _filename_from_remote_url(url: str, fallback_index: int) -> str:
    parsed = _validate_remote_url(url)
    host = (parsed.netloc or "").lower().split(":")[0]

    if _is_youtube_host(host):
        video_id = re.sub(r"[^A-Za-z0-9_-]", "", _extract_youtube_video_id(parsed))[:32]
        suffix = video_id or f"url_{fallback_index}"
        return f"youtube_{suffix}.mp4"

    candidate = Path(urllib.parse.unquote(parsed.path or "")).name
    if candidate:
        safe_name = sanitize_filename(candidate, fallback_ext=".mp4")
        if not Path(safe_name).suffix:
            safe_name = f"{safe_name}.mp4"
        return safe_name

    return f"video_{fallback_index}.mp4"


def _remove_file_if_exists(path: str) -> None:
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def _has_video_stream(path: str) -> bool:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_type",
        "-of",
        "json",
        path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except Exception:
        return False

    if result.returncode != 0:
        return False
    try:
        parsed = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return False
    return bool(parsed.get("streams"))


def _validate_media_upload_metadata(file: UploadFile) -> tuple[str, str]:
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_MEDIA_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_MEDIA_EXTENSIONS))
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file extension for upload. Allowed: {allowed}.",
        )

    content_type = (file.content_type or "").split(";")[0].strip().lower()
    if content_type and content_type not in ALLOWED_MEDIA_CONTENT_TYPES:
        allowed_types = ", ".join(sorted(ALLOWED_MEDIA_CONTENT_TYPES))
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported content type for upload. Allowed: {allowed_types}.",
        )

    media_type = "image" if extension in ALLOWED_IMAGE_EXTENSIONS else "video"
    return extension, media_type


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
async def add_uploads(project_id: str, req: AddUrlsRequest, request: Request, user=Depends(get_current_user)):
    """Add media URLs to a project. Creates upload records with PENDING status."""
    await verify_project_ownership(project_id, user)
    db = get_db()
    project_oid = parse_object_id(project_id, "project_id")
    now = datetime.datetime.utcnow()
    idempotency_context, replay = await begin_idempotent_operation(
        request=request,
        user_id=user["_id"],
        payload={
            "project_id": project_id,
            "urls": req.urls,
        },
    )
    if replay is not None:
        return replay.body

    try:
        # Get current max order
        last = await db.uploads.find_one(
            {"projectId": project_id},
            sort=[("order", -1)]
        )
        start_order = (last["order"] + 1) if last else 0

        created = []
        for i, url in enumerate(req.urls):
            normalized_url = (url or "").strip()
            inferred_filename = _filename_from_remote_url(normalized_url, start_order + i)
            upload = {
                "projectId": project_id,
                "userId": user["_id"],
                "originalUrl": normalized_url,
                "localPath": None,
                "previewPath": None,
                "thumbnailPath": None,
                "filename": inferred_filename,
                "fileSize": None,
                "duration": None,
                "status": "PENDING",
                "mediaType": "unknown",
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

        response = {"uploads": created, "total": count}
        await complete_idempotent_operation(idempotency_context, status_code=200, response_body=response)
        return response
    except Exception as exc:
        await fail_idempotent_operation(idempotency_context, error_message=str(exc))
        raise

@router.post("/file")
async def upload_local_file(project_id: str, request: Request, file: UploadFile = File(...), user=Depends(get_current_user)):
    """Handle raw video/photo uploads directly."""
    await verify_project_ownership(project_id, user)
    db = get_db()
    project_oid = parse_object_id(project_id, "project_id")
    settings = get_settings()
    now = datetime.datetime.utcnow()
    idempotency_context, replay = await begin_idempotent_operation(
        request=request,
        user_id=user["_id"],
        payload={
            "project_id": project_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "kind": "video_file_upload",
        },
    )
    if replay is not None:
        return replay.body

    try:
        # 1. Save File Locally
        extension, media_type = _validate_media_upload_metadata(file)
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
        if media_type == "video":
            has_video_stream = await asyncio.to_thread(_has_video_stream, local_path)
            if not has_video_stream:
                _remove_file_if_exists(local_path)
                raise HTTPException(status_code=415, detail="Uploaded file is not a valid video stream.")

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
            "mediaType": media_type,
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

        response = {"uploads": [upload], "total": count}
        await complete_idempotent_operation(idempotency_context, status_code=200, response_body=response)
        return response
    except Exception as exc:
        await fail_idempotent_operation(idempotency_context, error_message=str(exc))
        raise


@router.post("/music")
async def upload_custom_music(project_id: str, request: Request, file: UploadFile = File(...), user=Depends(get_current_user)):
    """Handle custom music uploads (.mp3, .wav, .m4a)."""
    await verify_project_ownership(project_id, user)
    settings = get_settings()
    idempotency_context, replay = await begin_idempotent_operation(
        request=request,
        user_id=user["_id"],
        payload={
            "project_id": project_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "kind": "music_file_upload",
        },
    )
    if replay is not None:
        return replay.body

    ext = Path(file.filename or "").suffix.lower()
    try:
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
        response = {"message": "Music uploaded successfully", "localPath": local_path, "filename": safe_name}
        await complete_idempotent_operation(idempotency_context, status_code=200, response_body=response)
        return response
    except Exception as exc:
        await fail_idempotent_operation(idempotency_context, error_message=str(exc))
        raise

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
async def delete_upload(project_id: str, upload_id: str, request: Request, user=Depends(get_current_user)):
    """Remove a single upload from the project."""
    await verify_project_ownership(project_id, user)
    db = get_db()
    idempotency_context, replay = await begin_idempotent_operation(
        request=request,
        user_id=user["_id"],
        payload={
            "project_id": project_id,
            "upload_id": upload_id,
        },
    )
    if replay is not None:
        return replay.body

    try:
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

        response = {"message": "Upload deleted", "total": count}
        await complete_idempotent_operation(idempotency_context, status_code=200, response_body=response)
        return response
    except Exception as exc:
        await fail_idempotent_operation(idempotency_context, error_message=str(exc))
        raise


@router.patch("/reorder")
async def reorder_uploads(project_id: str, req: ReorderRequest, request: Request, user=Depends(get_current_user)):
    """Reorder uploads by providing an ordered list of upload IDs."""
    await verify_project_ownership(project_id, user)
    db = get_db()
    idempotency_context, replay = await begin_idempotent_operation(
        request=request,
        user_id=user["_id"],
        payload={
            "project_id": project_id,
            "upload_ids": req.upload_ids,
        },
    )
    if replay is not None:
        return replay.body

    try:
        for i, uid in enumerate(req.upload_ids):
            upload_oid = parse_object_id(uid, "upload_id")
            await db.uploads.update_one(
                {"_id": upload_oid, "projectId": project_id},
                {"$set": {"order": i}}
            )

        await invalidate_after_upload_mutation(user["_id"], project_id)
        response = {"message": "Reordered", "order": req.upload_ids}
        await complete_idempotent_operation(idempotency_context, status_code=200, response_body=response)
        return response
    except Exception as exc:
        await fail_idempotent_operation(idempotency_context, error_message=str(exc))
        raise
