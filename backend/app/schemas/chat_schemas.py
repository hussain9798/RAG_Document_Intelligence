"""Pydantic request/response models for chat / RAG endpoints."""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    document_ids: list[str] | None = None
    conversation_id: str | None = None


class SourceItem(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    page_number: int
    score: float
    text: str


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    sources: list[SourceItem]


class ConversationPublic(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class MessagePublic(BaseModel):
    id: str
    role: str
    content: str
    sources: list[SourceItem]
    created_at: str
