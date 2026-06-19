from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List
import os
import re
import uuid
from pathlib import Path
import urllib.parse
from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..core.mongo_utils import parse_object_id
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

    return {"uploads": created, "total": count}

@router.post("/file")
async def upload_local_file(project_id: str, file: UploadFile = File(...), user=Depends(get_current_user)):
    """Handle raw video file uploads directly."""
    await verify_project_ownership(project_id, user)
    db = get_db()
    project_oid = parse_object_id(project_id, "project_id")
    now = datetime.datetime.utcnow()

    # 1. Save File Locally
    extension = Path(file.filename or "").suffix or ".mp4"
    clean_filename = sanitize_filename(file.filename or "", fallback_ext=extension)
    project_dir = f"data/{project_id}/downloads"
    os.makedirs(project_dir, exist_ok=True)
    local_path = os.path.join(project_dir, clean_filename)
    
    # We use sync file write for simplicity, chunked is better for huge files but this works for demo
    contents = await file.read()
    with open(local_path, "wb") as f:
        f.write(contents)

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
        "fileSize": len(contents),
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

    return {"uploads": [upload], "total": count}


@router.post("/music")
async def upload_custom_music(project_id: str, file: UploadFile = File(...), user=Depends(get_current_user)):
    """Handle custom music uploads (.mp3, .wav, .m4a)."""
    await verify_project_ownership(project_id, user)
    ext = Path(file.filename or "").suffix.lower()
    if ext not in {".mp3", ".wav", ".m4a"}:
        raise HTTPException(status_code=400, detail="Unsupported audio format")
    
    # 1. Save File Locally
    music_dir = f"data/{project_id}/music"
    os.makedirs(music_dir, exist_ok=True)
    safe_name = sanitize_filename(file.filename or "", fallback_ext=ext or ".mp3")
    local_path = os.path.join(music_dir, safe_name)
    
    contents = await file.read()
    with open(local_path, "wb") as f:
        f.write(contents)
        
    return {"message": "Music uploaded successfully", "localPath": local_path, "filename": safe_name}

@router.get("")
async def list_uploads(project_id: str, user=Depends(get_current_user)):
    """List all uploads for a project, sorted by order."""
    await verify_project_ownership(project_id, user)
    db = get_db()

    cursor = db.uploads.find({"projectId": project_id}).sort("order", 1)
    uploads = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        uploads.append(doc)

    return {"uploads": uploads, "total": len(uploads)}


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

    return {"message": "Reordered", "order": req.upload_ids}
