"""Document endpoints: upload, list, get, delete. All scoped to the authenticated user."""
import os

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status

from app.auth.dependencies import get_current_user
from app.config import get_settings
from app.database.mongodb import get_database
from app.models.document import document_to_public, new_document_record
from app.schemas.document_schemas import DocumentListResponse, DocumentPublic
from app.services.document_pipeline import process_document
from app.services.vector_store import delete_positions
from app.utils.files import resolve_within, safe_filename
from app.utils.logger import get_logger

router = APIRouter(prefix="/api/documents", tags=["documents"])
logger = get_logger("rag.api.documents")


@router.post("/upload", response_model=DocumentPublic, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    current_user: dict = Depends(get_current_user),
):
    settings = get_settings()

    if file.content_type not in ("application/pdf",) and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed.")

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.max_upload_mb:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds the {settings.max_upload_mb}MB upload limit.",
        )
    if len(contents) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    os.makedirs(settings.upload_dir, exist_ok=True)
    stored_name = safe_filename(file.filename)
    file_path = resolve_within(settings.upload_dir, stored_name)

    with open(file_path, "wb") as f:
        f.write(contents)

    db = get_database()
    user_id = str(current_user["_id"])
    doc_record = new_document_record(user_id, file.filename, file_path, len(contents))
    result = await db.documents.insert_one(doc_record)
    doc_record["_id"] = result.inserted_id

    logger.info("Document uploaded: %s by user %s", result.inserted_id, user_id)

    background_tasks.add_task(process_document, str(result.inserted_id), user_id, file_path)

    return DocumentPublic(**document_to_public(doc_record))


@router.get("", response_model=DocumentListResponse)
async def list_documents(current_user: dict = Depends(get_current_user)):
    db = get_database()
    user_id = str(current_user["_id"])
    cursor = db.documents.find({"user_id": user_id}).sort("created_at", -1)
    docs = [document_to_public(d) async for d in cursor]
    return DocumentListResponse(documents=[DocumentPublic(**d) for d in docs], total=len(docs))


async def _get_owned_document(db, document_id: str, user_id: str) -> dict:
    try:
        oid = ObjectId(document_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    doc = await db.documents.find_one({"_id": oid, "user_id": user_id})
    if doc is None:
        # Same error for "doesn't exist" and "belongs to someone else" - never
        # leak whether a document id exists for another user.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return doc


@router.get("/{document_id}", response_model=DocumentPublic)
async def get_document(document_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    doc = await _get_owned_document(db, document_id, str(current_user["_id"]))
    return DocumentPublic(**document_to_public(doc))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    user_id = str(current_user["_id"])
    doc = await _get_owned_document(db, document_id, user_id)

    chunk_cursor = db.chunks.find({"document_id": document_id, "user_id": user_id})
    faiss_positions = [c["faiss_index"] async for c in chunk_cursor]

    if faiss_positions:
        delete_positions(faiss_positions)

    await db.chunks.delete_many({"document_id": document_id, "user_id": user_id})
    await db.documents.delete_one({"_id": doc["_id"], "user_id": user_id})

    try:
        if os.path.exists(doc["file_path"]):
            os.remove(doc["file_path"])
    except OSError:
        logger.warning("Could not remove file for deleted document %s", document_id)

    logger.info("Document deleted: %s by user %s", document_id, user_id)
    return None
