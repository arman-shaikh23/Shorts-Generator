from fastapi import APIRouter, Depends
from bson import ObjectId

from ..core.cache import build_history_cache_key, cache_get, cache_set
from ..core.config import get_settings
from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..core.pagination import build_pagination_meta, normalize_limit, resolve_page_skip

router = APIRouter(prefix="/history", tags=["History"])

@router.get("/")
async def get_history(
    page: int = 1,
    limit: int = 12,
    skip: int | None = None,
    user = Depends(get_current_user)
):
    """Get all generated shorts for the current user."""
    db = get_db()
    settings = get_settings()
    safe_limit = normalize_limit(limit, default_limit=12, max_limit=100)
    safe_page, safe_skip = resolve_page_skip(page=page, skip=skip, limit=safe_limit)
    cache_key = await build_history_cache_key(user["_id"], safe_page, safe_limit, safe_skip)
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached
    
    cursor = (
        db.generated_shorts.find({"userId": user["_id"]})
        .sort("createdAt", -1)
        .skip(safe_skip)
        .limit(safe_limit)
    )
    shorts = []
    
    # We also want to fetch project titles for context
    project_ids = []
    
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["userId"] = str(doc["userId"])
        doc["projectId"] = str(doc["projectId"])
        if ObjectId.is_valid(doc["projectId"]):
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
    pagination = build_pagination_meta(total=total_docs, page=safe_page, limit=safe_limit, skip=safe_skip)
    
    response = {
        "shorts": shorts,
        **pagination,
    }
    await cache_set(cache_key, response, settings.CACHE_TTL_HISTORY_SEC)
    return response
