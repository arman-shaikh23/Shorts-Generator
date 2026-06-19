import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from .config import get_settings

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

    client = AsyncIOMotorClient(
        mongo_url,
        maxPoolSize=max_pool_size,
        minPoolSize=min_pool_size,
        maxIdleTimeMS=settings.MONGO_MAX_IDLE_TIME_MS,
        waitQueueTimeoutMS=settings.MONGO_WAIT_QUEUE_TIMEOUT_MS,
        serverSelectionTimeoutMS=settings.MONGO_SERVER_SELECTION_TIMEOUT_MS,
    )
    # Fail fast at startup if the DB is not reachable.
    await client.admin.command("ping")
    db = client[db_name]
    logger.info(
        "[MONGO POOL] Connected to MongoDB db=%s maxPool=%s minPool=%s",
        db_name,
        max_pool_size,
        min_pool_size,
    )

async def close_mongo_connection():
    global client
    if client:
        client.close()
        logger.info("[MONGO POOL] Closed MongoDB client.")

def get_db():
    return db
