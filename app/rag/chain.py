"""
Portfolio RAG and direct context pipelines with conversation memory and fallback resilience.
"""

from __future__ import annotations

import logging
import time
from functools import lru_cache
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

from app.config import get_settings
from app.data.loader import get_portfolio
from app.rag.ingest import portfolio_to_documents
from app.rag.prompts import get_qa_prompt

logger = logging.getLogger(__name__)


def _get_llm():
    """
    Instantiate the configured LLM provider (Groq or Gemini)
    with a strict 20-second timeout to prevent hung requests.
    """
    settings = get_settings()
    if settings.llm_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=0.2,
            request_timeout=20.0,
        )

    from langchain_groq import ChatGroq

    return ChatGroq(
        model=settings.groq_model,
        groq_api_key=settings.groq_api_key,
        temperature=0.2,
        request_timeout=20.0,
    )


def _format_docs(docs) -> str:
    """Format retrieved Document chunks into a single context string."""
    return "\n\n".join(doc.page_content for doc in docs)


def _get_full_context() -> str:
    """Assemble all portfolio documents for Direct Context Mode (when vectorstore is absent)."""
    documents = portfolio_to_documents(get_portfolio())
    return _format_docs(documents)


def format_chat_history(history: list[dict[str, Any]] | None) -> list[BaseMessage]:
    """
    Convert raw conversation turns into LangChain BaseMessage objects.
    Enforces a maximum of 4 turns and truncates each message at 500 characters.
    """
    if not history:
        return []
    messages: list[BaseMessage] = []
    # Take only the last 4 turns
    for turn in history[-4:]:
        role = turn.get("role")
        content = (turn.get("content") or "").strip()
        if not content:
            continue
        content = content[:500]
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    return messages


@lru_cache
def get_direct_chain():
    """
    Direct Context chain for Groq/Gemini when FAISS embeddings are not configured.
    Injects full portfolio context directly into the prompt with conversation memory.
    """
    logger.info("Building direct context chain")
    context = _get_full_context()
    prompt = get_qa_prompt()
    llm = _get_llm()

    return (
        {
            "context": RunnableLambda(lambda _: context),
            "input": RunnableLambda(lambda x: x["input"] if isinstance(x, dict) else x),
            "chat_history": RunnableLambda(
                lambda x: x.get("chat_history", []) if isinstance(x, dict) else []
            ),
        }
        | prompt
        | llm
        | StrOutputParser()
    )


@lru_cache
def get_rag_chain():
    """
    RAG chain utilizing FAISS semantic similarity search and conversation memory.
    """
    logger.info("Building RAG chain")
    from app.rag.ingest import ensure_vectorstore

    vectorstore = ensure_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    prompt = get_qa_prompt()
    llm = _get_llm()

    return (
        {
            "context": RunnableLambda(lambda x: x["input"] if isinstance(x, dict) else x)
            | retriever
            | _format_docs,
            "input": RunnableLambda(lambda x: x["input"] if isinstance(x, dict) else x),
            "chat_history": RunnableLambda(
                lambda x: x.get("chat_history", []) if isinstance(x, dict) else []
            ),
        }
        | prompt
        | llm
        | StrOutputParser()
    )


def ask_portfolio(question: str, history: list[dict[str, Any]] | None = None) -> str:
    """
    Execute the portfolio QA pipeline with conversation history and fallback resilience.

    If the LLM call times out (20s) or encounters an error, a friendly fallback message
    containing direct contact methods (email and LinkedIn) is returned instead of raising a 500.
    """
    settings = get_settings()
    mode = chat_mode()
    logger.info("Pipeline start | mode=%s | question=%r", mode, question[:120])

    chat_history = format_chat_history(history)
    payload = {"input": question, "chat_history": chat_history}
    started = time.perf_counter()

    try:
        from pathlib import Path
        vectorstore_marker = Path(__file__).resolve().parent / "vectorstore" / "portfolio_faiss.faiss"

        if settings.google_api_key and vectorstore_marker.exists():
            try:
                reply = get_rag_chain().invoke(payload)
            except Exception as rag_err:
                logger.warning("RAG chain failed (%s); falling back to direct chain", rag_err)
                reply = get_direct_chain().invoke(payload)
        else:
            reply = get_direct_chain().invoke(payload)
    except Exception as exc:
        elapsed = time.perf_counter() - started
        logger.exception(
            "Pipeline failed or timed out | mode=%s | elapsed=%.2fs | error=%s",
            mode,
            elapsed,
            exc,
        )
        portfolio = get_portfolio()
        # Friendly contact fallback message
        return (
            f"I'm having trouble connecting to my AI service right now. "
            f"Please reach out directly to {portfolio.profile.name} via email at "
            f"{portfolio.profile.email} or on LinkedIn at {portfolio.social.linkedin}."
        )

    elapsed = time.perf_counter() - started
    logger.info(
        "Pipeline done | mode=%s | elapsed=%.2fs | reply_len=%d",
        mode,
        elapsed,
        len(reply),
    )
    return reply


def chat_mode() -> str:
    """Determine whether RAG mode or Direct Context Mode is active."""
    return "rag" if get_settings().google_api_key else "direct"
