from __future__ import annotations

import logging
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.data.loader import get_portfolio
from app.data.models import PortfolioData

logger = logging.getLogger(__name__)

VECTORSTORE_DIR = Path(__file__).resolve().parent / "vectorstore"
INDEX_NAME = "portfolio_faiss"


def portfolio_to_documents(portfolio: PortfolioData) -> list[Document]:
    docs: list[Document] = []

    profile_text = (
        f"Name: {portfolio.profile.name}\n"
        f"Title: {portfolio.profile.title}\n"
        f"Location: {portfolio.profile.location}\n"
        f"Experience: {portfolio.profile.experience_years} year(s)\n"
        f"Email: {portfolio.profile.email}\n"
        f"Bio: {portfolio.profile.bio}"
    )
    docs.append(Document(page_content=f"[PROFILE]\n{profile_text}", metadata={"section": "profile"}))

    skills_text = "\n".join(
        [
            "Core: " + ", ".join(portfolio.skills.core),
            "Frameworks: " + ", ".join(portfolio.skills.frameworks),
            "MLOps: " + ", ".join(portfolio.skills.mlops),
            "Databases: " + ", ".join(portfolio.skills.databases),
            "Tools: " + ", ".join(portfolio.skills.tools),
        ]
    )
    docs.append(Document(page_content=f"[SKILLS]\n{skills_text}", metadata={"section": "skills"}))

    for item in portfolio.differentiators:
        docs.append(
            Document(page_content=f"[DIFFERENTIATOR]\n{item}", metadata={"section": "differentiator"})
        )

    for project in portfolio.projects:
        proprietary = "proprietary" if project.is_proprietary else "open-source"
        content = (
            f"Title: {project.title}\n"
            f"Type: {proprietary}\n"
            f"Problem: {project.problem}\n"
            f"Description: {project.description}\n"
            f"Role: {project.role}\n"
            f"Tech: {', '.join(project.tech_stack)}"
        )
        if project.company:
            content += f"\nCompany: {project.company}"
        docs.append(
            Document(page_content=f"[PROJECT:{project.id}]\n{content}", metadata={"section": "project"})
        )

    for job in portfolio.experience:
        bullets = "\n".join(f"- {b}" for b in job.bullets)
        content = (
            f"Title: {job.title}\n"
            f"Company: {job.company}\n"
            f"Duration: {job.duration}\n"
            f"Location: {job.location}\n"
            f"Responsibilities:\n{bullets}"
        )
        docs.append(
            Document(page_content=f"[EXPERIENCE]\n{content}", metadata={"section": "experience"})
        )

    for edu in portfolio.education:
        docs.append(
            Document(
                page_content=f"[EDUCATION]\n{edu.degree} at {edu.institution} ({edu.duration})",
                metadata={"section": "education"},
            )
        )

    if portfolio.certifications:
        certs = "\n".join(f"- {c}" for c in portfolio.certifications)
        docs.append(Document(page_content=f"[CERTIFICATIONS]\n{certs}", metadata={"section": "certs"}))

    knowledge_dir = Path(__file__).resolve().parent / "knowledge"
    for path in sorted(knowledge_dir.glob("*.txt")):
        docs.append(
            Document(
                page_content=f"[KNOWLEDGE]\n{path.read_text(encoding='utf-8')}",
                metadata={"section": "knowledge", "source": path.name},
            )
        )

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    logger.debug("Portfolio documents prepared | sections=%d | chunks=%d", len(docs), len(chunks))
    return chunks


def get_embeddings():
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    from app.config import get_settings

    settings = get_settings()
    if not settings.google_api_key:
        raise RuntimeError("GOOGLE_API_KEY is required for embeddings.")
    return GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=settings.google_api_key,
    )


def build_vectorstore(force: bool = False):
    from langchain_community.vectorstores import FAISS

    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
    index_path = VECTORSTORE_DIR / f"{INDEX_NAME}.faiss"
    if index_path.exists() and not force:
        logger.info("Vectorstore index exists — loading from disk")
        return load_vectorstore()

    logger.info("Building vectorstore index from portfolio data")
    portfolio = get_portfolio()
    documents = portfolio_to_documents(portfolio)
    logger.info("Embedding %d document chunks", len(documents))
    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local(str(VECTORSTORE_DIR), INDEX_NAME)
    logger.info("Vectorstore saved | path=%s", VECTORSTORE_DIR)
    return vectorstore


def load_vectorstore():
    from langchain_community.vectorstores import FAISS

    logger.info("Loading vectorstore from %s", VECTORSTORE_DIR)
    embeddings = get_embeddings()
    return FAISS.load_local(
        str(VECTORSTORE_DIR),
        embeddings,
        INDEX_NAME,
        allow_dangerous_deserialization=True,
    )


def ensure_vectorstore(force: bool = False):
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
    index_path = VECTORSTORE_DIR / f"{INDEX_NAME}.faiss"
    if index_path.exists() and not force:
        return load_vectorstore()
    return build_vectorstore(force=force)
