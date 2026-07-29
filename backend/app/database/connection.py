import logging
from typing import AsyncGenerator, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger("physioverse.database")


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


# Global database state container
db = MongoDB()


async def connect_to_mongo():
    """Connect to MongoDB Atlas and initialize collection indexes."""
    try:
        logger.info("Connecting to MongoDB Atlas...")
        logger.debug(f"Connection URL: {settings.MONGODB_URL[:80]}...")

        db.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
        )
        db.db = db.client[settings.DATABASE_NAME]

        # Test connection
        await db.client.admin.command("ping")
        logger.info("✅ MongoDB Atlas connection successful")
        logger.info(f"✅ Database connected: {db.db.name}")

        # Create collection indexes
        await create_indexes()
        logger.info("✅ Database indexes created")

    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {str(e)}")
        logger.error(f"Connection string (partial): {settings.MONGODB_URL[:100]}...")
        raise


async def close_mongo_connection():
    """Close MongoDB connection on application shutdown."""
    if db.client:
        db.client.close()
        logger.info("✅ MongoDB connection closed")


async def create_indexes():
    """Create collection indexes safely on startup."""
    try:
        if db.db is not None:
            await db.db["users"].create_index("email", unique=True)
            await db.db["users"].create_index("phone")
            await db.db["users"].create_index("role")
            await db.db["patients"].create_index("user_id", unique=True, sparse=True)
            await db.db["patients"].create_index("physiotherapist_id")
            await db.db["refresh_tokens"].create_index("token", unique=True)
            await db.db["refresh_tokens"].create_index("user_id")
            logger.info("✅ Users & Patients collection indexes verified")
    except Exception as e:
        logger.warning(f"Index creation warning: {str(e)}")


async def get_database() -> AsyncIOMotorDatabase:
    """Dependency provider returning Motor database instance."""
    if db.db is None:
        raise RuntimeError("Database connection is not initialized.")
    return db.db


async def get_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """FastAPI dependency yielding active Motor database."""
    yield await get_database()
