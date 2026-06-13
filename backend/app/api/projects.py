from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from bson import ObjectId
from ..core.database import get_db
from ..core.dependencies import get_current_user
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
    project["_id"] = str(result.inserted_id)

    return project


@router.get("")
async def list_projects(user=Depends(get_current_user), skip: int = 0, limit: int = 50):
    db = get_db()

    cursor = db.projects.find({"userId": user["_id"]}).sort("updatedAt", -1).skip(skip).limit(limit)
    projects = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        projects.append(doc)

    total = await db.projects.count_documents({"userId": user["_id"]})

    return {"projects": projects, "total": total}


@router.get("/dashboard/stats")
async def get_dashboard_stats(user=Depends(get_current_user)):
    db = get_db()
    
    projects_count = await db.projects.count_documents({"userId": user["_id"]})
    videos_count = await db.uploads.count_documents({"userId": user["_id"]})
    scenes_count = await db.uploads.count_documents({"userId": user["_id"], "status": "PROCESSED"})
    exported_count = await db.generated_shorts.count_documents({"userId": user["_id"]})
    
    return {
        "projects": projects_count,
        "videos": videos_count,
        "scenes": scenes_count,
        "exported": exported_count
    }


@router.get("/{project_id}")
async def get_project(project_id: str, user=Depends(get_current_user)):
    db = get_db()

    project = await db.projects.find_one({"_id": ObjectId(project_id), "userId": user["_id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project["_id"] = str(project["_id"])

    # Get upload count
    project["uploadCount"] = await db.uploads.count_documents({"projectId": project_id})

    # Get generated shorts count
    project["generatedCount"] = await db.generated_shorts.count_documents({"projectId": project_id})

    return project


@router.patch("/{project_id}")
async def update_project(project_id: str, req: UpdateProjectRequest, user=Depends(get_current_user)):
    db = get_db()

    project = await db.projects.find_one({"_id": ObjectId(project_id), "userId": user["_id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update = {"updatedAt": datetime.datetime.utcnow()}
    if req.title is not None:
        update["title"] = req.title
    if req.tags is not None:
        update["tags"] = req.tags

    await db.projects.update_one({"_id": ObjectId(project_id)}, {"$set": update})

    project = await db.projects.find_one({"_id": ObjectId(project_id)})
    project["_id"] = str(project["_id"])
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: str, user=Depends(get_current_user)):
    db = get_db()

    project = await db.projects.find_one({"_id": ObjectId(project_id), "userId": user["_id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Delete associated uploads and shorts
    await db.uploads.delete_many({"projectId": project_id})
    await db.generated_shorts.delete_many({"projectId": project_id})
    await db.projects.delete_one({"_id": ObjectId(project_id)})

    return {"message": "Project deleted"}
