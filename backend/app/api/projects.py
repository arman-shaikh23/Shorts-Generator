from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from ..core.cache import (
    build_dashboard_stats_cache_key,
    build_project_detail_cache_key,
    build_projects_list_cache_key,
    cache_get,
    cache_set,
    invalidate_after_project_delete,
    invalidate_after_project_mutation,
)
from ..core.config import get_settings
from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..core.mongo_utils import parse_object_id
from ..core.pagination import build_pagination_meta, normalize_limit, resolve_page_skip
import datetime

router = APIRouter(prefix="/projects", tags=["Projects"])

# ── Request/Response Models ─────────────────────────────

class CreateProjectRequest(BaseModel):
    title: str

class UpdateProjectRequest(BaseModel):
    title: Optional[str] = None
    tags: Optional[List[str]] = None

# ── Endpoints ───────────────────────────────────────────

@router.post("")
async def create_project(req: CreateProjectRequest, user=Depends(get_current_user)):
    db = get_db()
    now = datetime.datetime.utcnow()

    project = {
        "userId": user["_id"],
        "title": req.title,
        "propertyType": None,
        "status": "DRAFT",
        "uploadCount": 0,
        "generatedCount": 0,
        "thumbnail": None,
        "tags": [],
        "createdAt": now,
        "updatedAt": now,
    }

    result = await db.projects.insert_one(project)
    project_id = str(result.inserted_id)
    project["_id"] = project_id
    await invalidate_after_project_mutation(user["_id"], project_id)

    return project


@router.get("")
async def list_projects(
    user=Depends(get_current_user),
    skip: int = 0,
    limit: int = 50,
    page: Optional[int] = None,
):
    db = get_db()
    settings = get_settings()
    safe_limit = normalize_limit(limit, default_limit=50, max_limit=100)
    safe_page, safe_skip = resolve_page_skip(page=page, skip=skip, limit=safe_limit)
    cache_key = await build_projects_list_cache_key(user["_id"], safe_page, safe_limit, safe_skip)
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    cursor = (
        db.projects.find({"userId": user["_id"]})
        .sort("updatedAt", -1)
        .skip(safe_skip)
        .limit(safe_limit)
    )
    projects = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        projects.append(doc)

    total = await db.projects.count_documents({"userId": user["_id"]})
    pagination = build_pagination_meta(total=total, page=safe_page, limit=safe_limit, skip=safe_skip)
    response = {"projects": projects, **pagination}
    await cache_set(cache_key, response, settings.CACHE_TTL_PROJECTS_SEC)
    return response


@router.get("/dashboard/stats")
async def get_dashboard_stats(user=Depends(get_current_user)):
    db = get_db()
    settings = get_settings()
    cache_key = await build_dashboard_stats_cache_key(user["_id"])
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached
    
    projects_count = await db.projects.count_documents({"userId": user["_id"]})
    videos_count = await db.uploads.count_documents({"userId": user["_id"]})
    scenes_count = await db.uploads.count_documents({"userId": user["_id"], "status": "PROCESSED"})
    exported_count = await db.generated_shorts.count_documents({"userId": user["_id"]})
    
    response = {
        "projects": projects_count,
        "videos": videos_count,
        "scenes": scenes_count,
        "exported": exported_count
    }
    await cache_set(cache_key, response, settings.CACHE_TTL_DASHBOARD_STATS_SEC)
    return response


@router.get("/{project_id}")
async def get_project(project_id: str, user=Depends(get_current_user)):
    db = get_db()
    project_oid = parse_object_id(project_id, "project_id")
    settings = get_settings()
    cache_key = await build_project_detail_cache_key(user["_id"], project_id)
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    project = await db.projects.find_one({"_id": project_oid, "userId": user["_id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project["_id"] = str(project["_id"])

    # Get upload count
    project["uploadCount"] = await db.uploads.count_documents({"projectId": project_id})

    # Get generated shorts count
    project["generatedCount"] = await db.generated_shorts.count_documents({"projectId": project_id})

    await cache_set(cache_key, project, settings.CACHE_TTL_PROJECT_DETAIL_SEC)
    return project


@router.patch("/{project_id}")
async def update_project(project_id: str, req: UpdateProjectRequest, user=Depends(get_current_user)):
    db = get_db()
    project_oid = parse_object_id(project_id, "project_id")

    project = await db.projects.find_one({"_id": project_oid, "userId": user["_id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update = {"updatedAt": datetime.datetime.utcnow()}
    if req.title is not None:
        update["title"] = req.title
    if req.tags is not None:
        update["tags"] = req.tags

    await db.projects.update_one({"_id": project_oid}, {"$set": update})

    project = await db.projects.find_one({"_id": project_oid})
    project["_id"] = str(project["_id"])
    await invalidate_after_project_mutation(user["_id"], project_id)
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: str, user=Depends(get_current_user)):
    db = get_db()
    project_oid = parse_object_id(project_id, "project_id")

    project = await db.projects.find_one({"_id": project_oid, "userId": user["_id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Delete associated uploads and shorts
    await db.uploads.delete_many({"projectId": project_id})
    await db.generated_shorts.delete_many({"projectId": project_id})
    await db.projects.delete_one({"_id": project_oid})

    # AGGRESSIVE STORAGE CLEANUP: Destroy the entire project data directory
    import shutil
    import os
    data_dir = os.path.abspath(os.path.join("data", project_id))
    data_root = os.path.abspath("data")
    if not data_dir.startswith(data_root + os.sep):
        raise HTTPException(status_code=400, detail="Invalid project directory path")
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir, ignore_errors=True)

    await invalidate_after_project_delete(user["_id"], project_id)
    return {"message": "Project deleted"}
