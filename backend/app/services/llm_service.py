"""
LLMService - provider-agnostic wrapper around whatever LLM API is configured.

Routes/other services only ever call `generate_answer()`. The actual
provider call (Google Gemini by default - it has a genuinely free tier) lives
here so the provider can be swapped later without touching the RAG pipeline.
"""
import google.generativeai as genai

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger("rag.llm_service")

SYSTEM_PROMPT = """You are a document question-answering assistant.

Answer the user's question using only the provided document context.
Do not invent facts. Do not use unsupported external knowledge.
If the answer cannot be found in the provided context, say exactly:
"I could not find this information in the uploaded documents."

Provide a concise and accurate answer. Reference the provided source
information (document name / page) naturally when it helps the answer,
but do not fabricate sources that are not in the given context."""

_configured_key: str | None = None


class LLMError(Exception):
    pass


def _build_context_block(chunks: list[dict]) -> str:
    if not chunks:
        return "(No relevant document context was found.)"
    parts = []
    for i, c in enumerate(chunks, start=1):
        parts.append(f"[Source {i}: {c['document_name']} - Page {c['page_number']}]\n{c['text']}")
    return "\n\n".join(parts)


def _build_history_block(history: list[dict]) -> str:
    if not history:
        return ""
    lines = []
    for m in history[-6:]:  # keep recent turns only to bound prompt size
        role = "User" if m["role"] == "user" else "Assistant"
        lines.append(f"{role}: {m['content']}")
    return "\n".join(lines)


def _ensure_configured(api_key: str) -> None:
    global _configured_key
    if _configured_key != api_key:
        genai.configure(api_key=api_key)
        _configured_key = api_key


def generate_answer(question: str, chunks: list[dict], history: list[dict] | None = None) -> str:
    """
    chunks: retrieved, user-scoped context chunks (already threshold-filtered).
    history: prior messages in this conversation, for continuity only -
             retrieved chunks remain the primary source of factual grounding.
    """
    settings = get_settings()

    if not chunks:
        # Don't even call the LLM with empty context - avoid any chance of
        # it "helpfully" answering from general knowledge.
        return "I could not find this information in the uploaded documents."

    if not settings.llm_api_key:
        raise LLMError(
            "LLM_API_KEY is not configured on the backend. Set it in your .env file to enable answer generation."
        )

    context_block = _build_context_block(chunks)
    history_block = _build_history_block(history or [])

    user_content = ""
    if history_block:
        user_content += f"Conversation so far:\n{history_block}\n\n"
    user_content += f"Document context:\n{context_block}\n\nQuestion: {question}"

    try:
        _ensure_configured(settings.llm_api_key)
        model = genai.GenerativeModel(
            model_name=settings.llm_model,
            system_instruction=SYSTEM_PROMPT,
        )
        response = model.generate_content(user_content)
        answer = (response.text or "").strip()
        if not answer:
            raise LLMError("LLM returned an empty response")
        return answer
    except LLMError:
        raise
    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        raise LLMError("The language model request failed. Please try again.") from exc