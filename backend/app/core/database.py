import os
import logging
import time
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from .config import get_settings
from .pool_observability import (
    configure_mongo_pool,
    get_mongo_event_listeners,
    mark_mongo_client_closed,
    mark_mongo_client_initialized,
    mongo_connect_failed,
    mongo_connect_succeeded,
    mongo_ping_failed,
    mongo_ping_succeeded,
)

client = None
db = None
logger = logging.getLogger(__name__)

async def _create_index_safe(collection, keys, **kwargs):
    """Create an index and log failures without crashing startup."""
    index_name = kwargs.get("name", "unnamed_index")
    try:
        await collection.create_index(keys, **kwargs)
        return True
    except Exception as exc:
        logger.warning(
            "[MONGO INDEX] Failed index creation collection=%s index=%s error=%s",
            collection.name,
            index_name,
            exc,
        )
        return False

async def ensure_database_indexes(db):
    """Ensure all critical query-path indexes exist."""
    index_specs = [
        # users
        (db.users, [("email", ASCENDING)], {"name": "users_email_uq", "unique": True}),

        # refresh_tokens
        (db.refresh_tokens, [("token", ASCENDING)], {"name": "refresh_token_uq", "unique": True}),
        (db.refresh_tokens, [("expires_at", ASCENDING)], {"name": "refresh_token_exp_ttl", "expireAfterSeconds": 0}),
        (db.refresh_tokens, [("family", ASCENDING), ("is_revoked", ASCENDING)], {"name": "refresh_family_revoked_idx"}),
        (db.refresh_tokens, [("user_id", ASCENDING), ("is_revoked", ASCENDING)], {"name": "refresh_user_revoked_idx"}),

        # projects
        (db.projects, [("userId", ASCENDING), ("updatedAt", DESCENDING)], {"name": "projects_user_updatedAt_idx"}),

        # uploads
        (db.uploads, [("projectId", ASCENDING), ("order", ASCENDING)], {"name": "uploads_project_order_idx"}),
        (db.uploads, [("projectId", ASCENDING), ("status", ASCENDING), ("order", ASCENDING)], {"name": "uploads_project_status_order_idx"}),
        (db.uploads, [("status", ASCENDING), ("uploadedAt", ASCENDING)], {"name": "uploads_status_uploadedAt_idx"}),
        (db.uploads, [("userId", ASCENDING), ("status", ASCENDING)], {"name": "uploads_user_status_idx"}),

        # generated_shorts
        (db.generated_shorts, [("userId", ASCENDING), ("createdAt", DESCENDING)], {"name": "shorts_user_createdAt_idx"}),
        (db.generated_shorts, [("projectId", ASCENDING)], {"name": "shorts_project_idx"}),
    ]

    success_count = 0
    for collection, keys, options in index_specs:
        created = await _create_index_safe(collection, keys, **options)
        if created:
            success_count += 1

    logger.info("[MONGO INDEX] Index ensure completed (%s/%s).", success_count, len(index_specs))

async def connect_to_mongo():
    global client, db
    settings = get_settings()
    mongo_url = os.environ.get("MONGODB_URL", settings.MONGODB_URL)
    db_name = os.environ.get("DB_NAME", settings.DB_NAME)
    max_pool_size = max(1, settings.MONGO_MAX_POOL_SIZE)
    min_pool_size = max(0, min(settings.MONGO_MIN_POOL_SIZE, max_pool_size))
    configure_mongo_pool(
        db_name=db_name,
        max_pool_size=max_pool_size,
        min_pool_size=min_pool_size,
        wait_queue_timeout_ms=settings.MONGO_WAIT_QUEUE_TIMEOUT_MS,
        server_selection_timeout_ms=settings.MONGO_SERVER_SELECTION_TIMEOUT_MS,
    )

    connect_started = time.perf_counter()
    try:
        listeners = get_mongo_event_listeners()
        client_kwargs = {
            "maxPoolSize": max_pool_size,
            "minPoolSize": min_pool_size,
            "maxIdleTimeMS": settings.MONGO_MAX_IDLE_TIME_MS,
            "waitQueueTimeoutMS": settings.MONGO_WAIT_QUEUE_TIMEOUT_MS,
            "serverSelectionTimeoutMS": settings.MONGO_SERVER_SELECTION_TIMEOUT_MS,
        }
        if listeners:
            client_kwargs["event_listeners"] = listeners

        client = AsyncIOMotorClient(
            mongo_url,
            **client_kwargs,
        )
        # Fail fast at startup if the DB is not reachable.
        ping_started = time.perf_counter()
        await client.admin.command("ping")
        ping_ms = (time.perf_counter() - ping_started) * 1000.0
        db = client[db_name]
        await ensure_database_indexes(db)

        connect_ms = (time.perf_counter() - connect_started) * 1000.0
        mark_mongo_client_initialized()
        mongo_connect_succeeded(connect_ms)
        mongo_ping_succeeded(ping_ms)
        logger.info(
            "[MONGO POOL] Connected to MongoDB db=%s maxPool=%s minPool=%s connectMs=%.2f pingMs=%.2f",
            db_name,
            max_pool_size,
            min_pool_size,
            connect_ms,
            ping_ms,
        )
    except Exception as exc:
        connect_ms = (time.perf_counter() - connect_started) * 1000.0
        mongo_connect_failed(connect_ms, exc)
        mongo_ping_failed(connect_ms, exc)
        raise

async def close_mongo_connection():
    global client, db
    if client:
        client.close()
        client = None
        db = None
        mark_mongo_client_closed()
        logger.info("[MONGO POOL] Closed MongoDB client.")

def get_db():
    return db
