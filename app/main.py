import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.config import get_settings
from app.core.logging_config import setup_logging
from app.data.loader import get_portfolio
from app.routes import chat, health, pages

load_dotenv()

settings = get_settings()
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.rag_ready = False
    app.state.chat_ready = False

    logger.info(
        "Starting portfolio app | env=%s | version=%s | llm_provider=%s",
        settings.env,
        __version__,
        settings.llm_provider,
    )

    if settings.chat_enabled:
        app.state.chat_ready = True
        model = settings.groq_model if settings.llm_provider == "groq" else settings.gemini_model
        logger.info("LLM configured | provider=%s | model=%s", settings.llm_provider, model)

        if settings.google_api_key:
            try:
                from app.rag.ingest import ensure_vectorstore

                ensure_vectorstore()
                app.state.rag_ready = True
                logger.info("Chat ready | mode=rag | vectorstore loaded")
            except Exception:
                logger.exception("RAG init failed — falling back to direct context mode")
        else:
            logger.info("Chat ready | mode=direct | no GOOGLE_API_KEY (full portfolio context injected)")
    else:
        logger.warning("Chat disabled | set GROQ_API_KEY or GOOGLE_API_KEY in .env")

    yield

    logger.info("Shutting down portfolio app")


def create_app() -> FastAPI:
    current_settings = get_settings()
    is_prod = current_settings.is_production

    from starlette.middleware.gzip import GZipMiddleware
    from app.core.middleware import SecurityHeadersMiddleware, StaticCacheMiddleware

    application = FastAPI(
        title="Sheikh Haseeb Portfolio",
        version=__version__,
        lifespan=lifespan,
        docs_url=None if is_prod else "/docs",
        redoc_url=None if is_prod else "/redoc",
        openapi_url=None if is_prod else "/openapi.json",
    )

    # Middleware execution order: last added is executed outermost.
    # We want: Client -> SecurityHeaders -> GZip -> StaticCache -> App
    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(GZipMiddleware, minimum_size=1000)
    application.add_middleware(StaticCacheMiddleware)

    application.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    application.include_router(pages.router)
    application.include_router(health.router)
    application.include_router(chat.router)

    @application.exception_handler(StarletteHTTPException)
    async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            accept = request.headers.get("accept", "")
            if (
                request.url.path.startswith("/api/")
                or request.url.path in ("/resume", "/resume/view")
                or "application/json" in accept
            ):
                return JSONResponse(status_code=404, content={"detail": exc.detail})
            try:
                portfolio = get_portfolio()
                return templates.TemplateResponse(
                    request=request,
                    name="404.html",
                    context={"portfolio": portfolio, "page_title": "404 — Page Not Found"},
                    status_code=404,
                )
            except Exception:
                return JSONResponse(status_code=404, content={"detail": exc.detail})
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    return application


app = create_app()
