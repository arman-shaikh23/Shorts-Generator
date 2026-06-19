from fastapi import APIRouter

from app.core.database import get_db
from app.core.pool_observability import get_pool_diagnostics

router = APIRouter(prefix="/health", tags=["Health"])

EXPECTED_INDEXES = {
    "users": {"users_email_uq"},
    "refresh_tokens": {
        "refresh_token_uq",
        "refresh_token_exp_ttl",
        "refresh_family_revoked_idx",
        "refresh_user_revoked_idx",
    },
    "projects": {"projects_user_updatedAt_idx"},
    "uploads": {
        "uploads_project_order_idx",
        "uploads_project_status_order_idx",
        "uploads_status_uploadedAt_idx",
        "uploads_user_status_idx",
    },
    "generated_shorts": {"shorts_user_createdAt_idx", "shorts_project_idx"},
}


@router.get("/pools")
async def pool_health() -> dict:
    """
    Read-only diagnostics for Mongo and outbound HTTP connection pools.
    """
    return get_pool_diagnostics()


@router.get("/indexes")
async def index_health() -> dict:
    """
    Read-only diagnostics for MongoDB index presence on critical collections.
    """
    db = get_db()
    if db is None:
        return {
            "status": "unavailable",
            "error": "database_not_connected",
            "collections": {},
            "missing_total": 0,
        }

    collections: dict[str, dict] = {}
    missing_total = 0

    for collection_name, expected_names in EXPECTED_INDEXES.items():
        collection = db[collection_name]
        try:
            docs = await collection.list_indexes().to_list(length=None)
            actual_indexes = []
            actual_names = set()
            for idx in docs:
                index_name = str(idx.get("name"))
                actual_names.add(index_name)
                actual_indexes.append(
                    {
                        "name": index_name,
                        "key": dict(idx.get("key", {})),
                        "unique": bool(idx.get("unique", False)),
                        "ttl_seconds": idx.get("expireAfterSeconds"),
                    }
                )
            missing = sorted(expected_names - actual_names)
            missing_total += len(missing)
            collections[collection_name] = {
                "expected_indexes": sorted(expected_names),
                "actual_indexes": actual_indexes,
                "missing_indexes": missing,
            }
        except Exception as exc:
            missing = sorted(expected_names)
            missing_total += len(missing)
            collections[collection_name] = {
                "expected_indexes": sorted(expected_names),
                "actual_indexes": [],
                "missing_indexes": missing,
                "error": str(exc),
            }

    return {
        "status": "ok" if missing_total == 0 else "degraded",
        "collections": collections,
        "missing_total": missing_total,
    }
