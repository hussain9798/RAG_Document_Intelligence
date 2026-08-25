"""
MongoDB Atlas connection management.

MongoDB Atlas is the source of truth for all application data and for the
metadata that maps FAISS vector positions back to chunks/documents/users.
FAISS itself never stores anything other than raw vectors + a lightweight
local mapping file (see services/vector_store.py).
"""
import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings

logger = logging.getLogger("rag.mongodb")

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def get_database() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database has not been initialized. Call connect_to_mongo() first.")
    return _db


async def connect_to_mongo() -> None:
    global _client, _db
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongodb_uri)
    _db = _client[settings.mongodb_database]

    # Verify connectivity early so the app fails fast with a clear error.
    await _client.admin.command("ping")
    logger.info("Connected to MongoDB Atlas database '%s'", settings.mongodb_database)

    await _ensure_indexes(_db)


async def close_mongo_connection() -> None:
    global _client
    if _client is not None:
        _client.close()
        logger.info("MongoDB connection closed")


async def _ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    """Create indexes required for correctness (unique email) and performance."""
    await db.users.create_index("email", unique=True)

    await db.documents.create_index("user_id")
    await db.documents.create_index("created_at")

    await db.chunks.create_index("document_id")
    await db.chunks.create_index("user_id")
    

    await db.conversations.create_index("user_id")
    await db.conversations.create_index("created_at")

    await db.messages.create_index("conversation_id")
    await db.messages.create_index("user_id")

    logger.info("MongoDB indexes ensured")
