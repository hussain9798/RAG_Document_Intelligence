"""
Chat / RAG endpoints.

POST /api/chat is the core RAG endpoint: validates the question, retrieves
user-scoped relevant chunks via retrieval_service, calls llm_service for a
grounded answer, and persists both the question and answer (with real
sources) to MongoDB.
"""
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.database.mongodb import get_database
from app.models.conversation import conversation_to_public, new_conversation_document
from app.models.message import ROLE_ASSISTANT, ROLE_USER, message_to_public, new_message_document
from app.schemas.chat_schemas import ChatRequest, ChatResponse, ConversationPublic, MessagePublic, SourceItem
from app.services.llm_service import LLMError, generate_answer
from app.services.retrieval_service import retrieve_relevant_chunks
from app.utils.logger import get_logger

router = APIRouter(tags=["chat"])
logger = get_logger("rag.api.chat")


async def _get_owned_conversation(db, conversation_id: str, user_id: str) -> dict:
    try:
        oid = ObjectId(conversation_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    convo = await db.conversations.find_one({"_id": oid, "user_id": user_id})
    if convo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return convo


@router.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, current_user: dict = Depends(get_current_user)):
    db = get_database()
    user_id = str(current_user["_id"])
    question = payload.question.strip()

    if not question:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question cannot be empty.")

    logger.info("Query received from user %s", user_id)

    # Resolve or create the conversation (always owned by this user).
    if payload.conversation_id:
        convo = await _get_owned_conversation(db, payload.conversation_id, user_id)
    else:
        title = question[:60] + ("..." if len(question) > 60 else "")
        convo_doc = new_conversation_document(user_id, title)
        result = await db.conversations.insert_one(convo_doc)
        convo_doc["_id"] = result.inserted_id
        convo = convo_doc

    conversation_id = str(convo["_id"])

    # Validate requested document_ids belong to this user, if provided.
    document_ids = payload.document_ids
    if document_ids:
        owned_count = await db.documents.count_documents(
            {"user_id": user_id, "_id": {"$in": [ObjectId(d) for d in document_ids]}}
        )
        if owned_count != len(set(document_ids)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more documents not found.")

    sources = await retrieve_relevant_chunks(user_id, question, document_ids)
    logger.info("Retrieval completed: %d chunks for conversation %s", len(sources), conversation_id)

    # Pull recent conversation history for continuity (not as factual grounding).
    history_cursor = db.messages.find({"conversation_id": conversation_id}).sort("created_at", 1)
    history = [{"role": m["role"], "content": m["content"]} async for m in history_cursor]

    try:
        answer = generate_answer(question, sources, history)
    except LLMError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    logger.info("LLM request completed for conversation %s", conversation_id)

    user_msg = new_message_document(conversation_id, user_id, ROLE_USER, question, [])
    assistant_msg = new_message_document(conversation_id, user_id, ROLE_ASSISTANT, answer, sources)
    await db.messages.insert_many([user_msg, assistant_msg])

    from datetime import datetime, timezone

    await db.conversations.update_one(
        {"_id": convo["_id"]}, {"$set": {"updated_at": datetime.now(timezone.utc)}}
    )

    return ChatResponse(
        conversation_id=conversation_id,
        answer=answer,
        sources=[SourceItem(**s) for s in sources],
    )


@router.get("/api/conversations", response_model=list[ConversationPublic])
async def list_conversations(current_user: dict = Depends(get_current_user)):
    db = get_database()
    user_id = str(current_user["_id"])
    cursor = db.conversations.find({"user_id": user_id}).sort("updated_at", -1)
    return [ConversationPublic(**conversation_to_public(c)) async for c in cursor]


@router.get("/api/conversations/{conversation_id}", response_model=list[MessagePublic])
async def get_conversation_messages(conversation_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    user_id = str(current_user["_id"])
    await _get_owned_conversation(db, conversation_id, user_id)

    cursor = db.messages.find({"conversation_id": conversation_id, "user_id": user_id}).sort("created_at", 1)
    return [MessagePublic(**message_to_public(m)) async for m in cursor]


@router.delete("/api/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    user_id = str(current_user["_id"])
    convo = await _get_owned_conversation(db, conversation_id, user_id)

    await db.messages.delete_many({"conversation_id": conversation_id, "user_id": user_id})
    await db.conversations.delete_one({"_id": convo["_id"], "user_id": user_id})
    return None
