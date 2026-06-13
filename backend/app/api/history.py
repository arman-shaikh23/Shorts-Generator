from fastapi import APIRouter, Depends, HTTPException
from typing import List
from bson import ObjectId
import math

from ..core.database import get_db
from ..core.dependencies import get_current_user

router = APIRouter(prefix="/history", tags=["History"])

@router.get("/")
async def get_history(
    page: int = 1, 
    limit: int = 12, 
    user = Depends(get_current_user)
):
    """Get all generated shorts for the current user."""
    db = get_db()
    skip = (page - 1) * limit
    
    cursor = db.generated_shorts.find({"userId": user["_id"]}).sort("createdAt", -1).skip(skip).limit(limit)
    shorts = []
    
    # We also want to fetch project titles for context
    project_ids = []
    
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["userId"] = str(doc["userId"])
        doc["projectId"] = str(doc["projectId"])
        project_ids.append(ObjectId(doc["projectId"]))
        shorts.append(doc)
        
    # Batch fetch projects
    projects_map = {}
    if project_ids:
        proj_cursor = db.projects.find({"_id": {"$in": project_ids}})
        async for p in proj_cursor:
            projects_map[str(p["_id"])] = p.get("title", "Unknown Project")
            
    for short in shorts:
        short["projectTitle"] = projects_map.get(short["projectId"], "Unknown Project")
        
    total_docs = await db.generated_shorts.count_documents({"userId": user["_id"]})
    
    return {
        "shorts": shorts,
        "page": page,
        "limit": limit,
        "total": total_docs,
        "pages": math.ceil(total_docs / limit)
    }
