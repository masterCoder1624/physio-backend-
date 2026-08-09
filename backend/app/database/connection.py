import logging
import re
from typing import AsyncGenerator, Optional
import certifi
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger("physioverse.database")


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


# Global database state container
db = MongoDB()


def _sanitize_uri(uri: str) -> str:
    """Mask password in MongoDB connection URI for secure logging."""
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:****@", uri)


async def connect_to_mongo():
    """Connect to MongoDB Atlas with valid CA certificates and initialize collection indexes."""
    try:
        masked_uri = _sanitize_uri(settings.MONGODB_URL)
        logger.info("Connecting to MongoDB Atlas...")
        logger.debug(f"Connection URI: {masked_uri[:80]}...")

        # PyMongo / Motor client configuration with explicit certifi CA bundle
        client_kwargs = {
            "maxPoolSize": 50,
            "minPoolSize": 10,
            "serverSelectionTimeoutMS": 10000,
            "connectTimeoutMS": 10000,
        }

        # Apply certifi CA bundle for TLS/SSL connections to prevent Linux/Render OpenSSL TLS handshake failures
        if "mongodb+srv://" in settings.MONGODB_URL or "tls=true" in settings.MONGODB_URL.lower() or "ssl=true" in settings.MONGODB_URL.lower():
            client_kwargs["tlsCAFile"] = certifi.where()

        db.client = AsyncIOMotorClient(settings.MONGODB_URL, **client_kwargs)
        db.db = db.client[settings.DATABASE_NAME]

        # Test connection ping
        await db.client.admin.command("ping")
        logger.info("✅ MongoDB Atlas connection successful")
        logger.info(f"✅ Database connected: {db.db.name}")

        # Create collection indexes
        await create_indexes()
        logger.info("✅ Database indexes created")

    except Exception as e:
        masked_uri = _sanitize_uri(settings.MONGODB_URL)
        logger.error(f"❌ MongoDB connection failed: {str(e)}")
        logger.error(f"Connection URI (sanitized): {masked_uri[:80]}...")
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
            await db.db["patients"].create_index("user_id")
            await db.db["patients"].create_index("physiotherapist_id")
            await db.db["invoices"].create_index("patient_id")
            await db.db["invoices"].create_index(
                [("patient_id", 1), ("generation_key", 1)],
                unique=True,
                partialFilterExpression={"generation_key": {"$exists": True}},
            )
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
