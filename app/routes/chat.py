import logging
import time

from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.config import get_settings
from app.core.rate_limit import get_rate_limiter
from app.data.loader import get_portfolio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/config")
async def chat_config():
    portfolio = get_portfolio()
    chips = (
        portfolio.chat.suggestion_chips
        if portfolio.chat and portfolio.chat.suggestion_chips
        else portfolio.assistant.suggested_questions
    )
    return {
        "assistant_name": portfolio.assistant.name,
        "assistant_initials": portfolio.assistant.initials,
        "suggestion_chips": chips,
        "current_status": portfolio.profile.current_status,
        "availability": portfolio.profile.availability,
        "last_updated": portfolio.profile.last_updated,
    }


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=500)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    history: list[ChatTurn] = Field(default_factory=list, max_length=4)


class ChatResponse(BaseModel):
    reply: str


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest):
    settings = get_settings()
    client_ip = _client_ip(request)
    message = body.message.strip()
    started = time.perf_counter()

    logger.info("Chat API hit | ip=%s | message=%r", client_ip, message[:120])

    if not settings.chat_enabled:
        logger.warning("Chat rejected | ip=%s | reason=chat_disabled", client_ip)
        raise HTTPException(
            status_code=503,
            detail="Chatbot is unavailable — add GROQ_API_KEY or GOOGLE_API_KEY to .env",
        )

    if not getattr(request.app.state, "chat_ready", False):
        logger.warning("Chat rejected | ip=%s | reason=not_ready", client_ip)
        raise HTTPException(status_code=503, detail="Chatbot is still initializing. Please try again shortly.")

    limiter = get_rate_limiter()
    if not limiter.is_allowed(client_ip):
        logger.warning("Chat rate limited | ip=%s", client_ip)
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")

    try:
        from app.rag.chain import ask_portfolio

        history_data = [turn.model_dump() for turn in body.history]
        reply = ask_portfolio(message, history=history_data)
    except Exception:
        elapsed = time.perf_counter() - started
        logger.exception("Chat API failed | ip=%s | elapsed=%.2fs", client_ip, elapsed)
        portfolio = get_portfolio()
        reply = (
            f"I'm having trouble connecting to my AI service right now. "
            f"Please reach out directly to {portfolio.profile.name} via email at "
            f"{portfolio.profile.email} or on LinkedIn at {portfolio.social.linkedin}."
        )

    elapsed = time.perf_counter() - started
    logger.info(
        "Chat API ok | ip=%s | elapsed=%.2fs | reply_len=%d | preview=%r",
        client_ip,
        elapsed,
        len(reply),
        reply[:100],
    )
    return ChatResponse(reply=reply)
