import os
import logging
import time
from motor.motor_asyncio import AsyncIOMotorClient
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
