import os
from motor.motor_asyncio import AsyncIOMotorClient

client = None
db = None

async def connect_to_mongo():
    global client, db
    mongo_url = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    db = client.realestate_shorts
    print("Connected to MongoDB!")

async def close_mongo_connection():
    global client
    if client:
        client.close()
        print("Closed MongoDB connection.")

def get_db():
    return db
