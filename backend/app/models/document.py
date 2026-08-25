"""Mongo 'documents' collection shape + serialization helpers."""
from datetime import datetime, timezone

STATUS_UPLOADED = "uploaded"
STATUS_PROCESSING = "processing"
STATUS_PROCESSED = "processed"
STATUS_FAILED = "failed"


def new_document_record(user_id, filename: str, file_path: str, file_size: int) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "user_id": user_id,
        "filename": filename,
        "file_path": file_path,
        "file_size": file_size,
        "page_count": None,
        "status": STATUS_UPLOADED,
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }


def document_to_public(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "filename": doc["filename"],
        "file_size": doc["file_size"],
        "page_count": doc.get("page_count"),
        "status": doc["status"],
        "error_message": doc.get("error_message"),
        "created_at": doc["created_at"].isoformat(),
        "updated_at": doc["updated_at"].isoformat(),
    }
