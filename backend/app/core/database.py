import os
from motor.motor_asyncio import AsyncIOMotorClient

client = None
db = None

async def connect_to_mongo():
    global client, db
    mongo_url = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "realestate_shorts")
    client = AsyncIOMotorClient(mongo_url)
    # Fail fast at startup if the DB is not reachable.
    await client.admin.command("ping")
    db = client[db_name]
    print("Connected to MongoDB!")

async def close_mongo_connection():
    global client
    if client:
        client.close()
        print("Closed MongoDB connection.")

def get_db():
    return db
