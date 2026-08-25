"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, chat, documents
from app.config import get_settings
from app.database.mongodb import close_mongo_connection, connect_to_mongo
from app.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger("rag.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    await connect_to_mongo()
    logger.info("Application startup complete")
    yield
    await close_mongo_connection()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="RAG Document Intelligence API",
    description="Upload PDFs, ask questions, get grounded answers with citations.",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Never leak stack traces to the client; log full details server-side instead.
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected server error occurred."},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/api/health", tags=["health"])
async def health():
    return {"status": "ok"}
