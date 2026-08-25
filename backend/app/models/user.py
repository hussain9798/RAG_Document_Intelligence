"""
Mongo 'users' collection shape + serialization helpers.

We intentionally use plain dicts with PyMongo/Motor (per the spec: no
SQLAlchemy, no ORM) but centralize the document shape and the
Mongo-doc -> API-safe-dict conversion here so it isn't duplicated.
"""
from datetime import datetime, timezone


def new_user_document(name: str, email: str, password_hash: str) -> dict:
    return {
        "name": name,
        "email": email,
        "password_hash": password_hash,
        "created_at": datetime.now(timezone.utc),
    }


def user_to_public(doc: dict) -> dict:
    """Never include password_hash in anything returned to the client."""
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "email": doc["email"],
        "created_at": doc["created_at"].isoformat(),
    }
