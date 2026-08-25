"""Mongo 'messages' collection shape + serialization helpers."""
from datetime import datetime, timezone

ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"


def new_message_document(conversation_id, user_id, role: str, content: str, sources: list) -> dict:
    return {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "role": role,
        "content": content,
        "sources": sources,
        "created_at": datetime.now(timezone.utc),
    }


def message_to_public(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "role": doc["role"],
        "content": doc["content"],
        "sources": doc.get("sources", []),
        "created_at": doc["created_at"].isoformat(),
    }
