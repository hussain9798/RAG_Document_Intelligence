"""Mongo 'conversations' collection shape + serialization helpers."""
from datetime import datetime, timezone


def new_conversation_document(user_id, title: str) -> dict:
    now = datetime.now(timezone.utc)
    return {"user_id": user_id, "title": title, "created_at": now, "updated_at": now}


def conversation_to_public(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "title": doc["title"],
        "created_at": doc["created_at"].isoformat(),
        "updated_at": doc["updated_at"].isoformat(),
    }
