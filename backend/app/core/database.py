# backend/app/core/database.py

from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

class MongoDB:
    client: AsyncIOMotorClient = None

db = MongoDB()

async def connect_to_mongo():
    """Connects to the MongoDB database."""
    print("Connecting to MongoDB...")
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    print("Successfully connected to MongoDB.")

async def close_mongo_connection():
    """Closes the MongoDB connection."""
    print("Closing MongoDB connection...")
    db.client.close()
    print("MongoDB connection closed.")

def get_database():
    """Returns the database instance."""
    return db.client[settings.DATABASE_NAME]