"""
Centralized application configuration.

All values are loaded from environment variables (or a local .env file during
development). Nothing sensitive is hardcoded here - see .env.example for the
full list of variables the app expects.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # MongoDB
    mongodb_uri: str
    mongodb_database: str = "rag_document_intelligence"

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # LLM
    llm_provider: str = "anthropic"
    llm_api_key: str = ""
    llm_model: str = "claude-sonnet-4-6"

    # Embeddings (Google Gemini)
    gemini_api_key: str = ""

    # Storage
    upload_dir: str = "storage/uploads"

    # Chunking
    chunk_size_words: int = 600
    chunk_overlap_words: int = 120

    # Retrieval
    top_k: int = 5
    similarity_threshold: float = 0.35

    # CORS - comma separated origins
    cors_origins: str = "http://localhost:5173"

    # Uploads
    max_upload_mb: int = 25

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Settings are cached so the .env file is only parsed once per process."""
    return Settings()