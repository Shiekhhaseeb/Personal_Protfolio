from pathlib import Path

from fastapi import APIRouter, Request

from app import __version__
from app.config import get_settings

router = APIRouter(prefix="/api", tags=["health"])

VECTORSTORE_MARKER = (
    Path(__file__).resolve().parent.parent / "rag" / "vectorstore" / "portfolio_faiss.faiss"
)


@router.get("/health")
async def health_check(request: Request):
    settings = get_settings()
    rag_index_loaded = VECTORSTORE_MARKER.exists() or getattr(request.app.state, "rag_ready", False)
    return {
        "status": "ok",
        "version": __version__,
        "rag_index_loaded": rag_index_loaded,
        "chat_enabled": settings.chat_enabled,
        "chat_ready": getattr(request.app.state, "chat_ready", False),
        "llm_provider": settings.llm_provider,
    }
