import logging
import time
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.data.loader import get_portfolio

logger = logging.getLogger(__name__)

router = APIRouter(tags=["pages"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
RESUME_PATH = (
    Path(__file__).resolve().parent.parent / "static" / "resume" / "Sheikh_Haseeb_Resume.pdf"
)


@router.get("/resume", include_in_schema=False)
async def download_resume():
    if not RESUME_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Resume is currently unavailable. Please check back soon or contact me directly.",
        )
    logger.info("Resume download requested | timestamp=%s", time.time())
    portfolio = get_portfolio()
    clean_filename = f"{portfolio.profile.name.replace(' ', '_')}_Resume.pdf"
    return FileResponse(
        path=RESUME_PATH,
        media_type="application/pdf",
        filename=clean_filename,
    )


@router.get("/resume/view", include_in_schema=False)
async def view_resume():
    if not RESUME_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Resume is currently unavailable. Please check back soon or contact me directly.",
        )
    logger.info("Resume inline view requested | timestamp=%s", time.time())
    return FileResponse(
        path=RESUME_PATH,
        media_type="application/pdf",
    )


@router.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    portfolio = get_portfolio()
    content = f"""User-agent: *
Allow: /
Disallow: /api/

Sitemap: {portfolio.seo.site_url.rstrip('/')}/sitemap.xml
"""
    return PlainTextResponse(content.strip() + "\n", media_type="text/plain")


@router.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml():
    portfolio = get_portfolio()
    site_url = portfolio.seo.site_url.rstrip("/")
    lastmod = portfolio.profile.last_updated
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{site_url}/</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{site_url}/resume/view</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>
"""
    return Response(content=xml.strip() + "\n", media_type="application/xml")


@router.get("/")
async def home(request: Request):
    portfolio = get_portfolio()
    settings = get_settings()
    email = portfolio.profile.email
    body = quote(f"Hi, {portfolio.profile.name},\n\n")
    mailto_url = f"mailto:{email}?body={body}"
    gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={quote(email)}&body={body}"
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "portfolio": portfolio,
            "page_title": f"{portfolio.profile.name} — {portfolio.profile.title}",
            "chat_enabled": settings.chat_enabled,
            "mailto_url": mailto_url,
            "gmail_url": gmail_url,
        },
    )
