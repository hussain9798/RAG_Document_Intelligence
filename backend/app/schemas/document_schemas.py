"""Pydantic request/response models for document endpoints."""
from pydantic import BaseModel


class DocumentPublic(BaseModel):
    id: str
    filename: str
    file_size: int
    page_count: int | None = None
    status: str
    error_message: str | None = None
    created_at: str
    updated_at: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentPublic]
    total: int
