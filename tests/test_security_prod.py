"""
Tests for Phase 5: Security and production config.

Covers:
- Docs disabling in production (/docs, /redoc, /openapi.json)
- Rate limiter proxy safe IP extraction (TRUSTED_PROXY_COUNT & spoofed headers)
- Security headers (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, CSP)
- GZip compression and static asset long-cache headers
- App startup without GOOGLE_API_KEY / FAISS index in Direct Context Mode
"""

from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app


def test_docs_enabled_in_development(monkeypatch):
    from app.config import get_settings
    get_settings.cache_clear()
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("ENVIRONMENT", "development")
    dev_app = create_app()
    with TestClient(dev_app) as client:
        res = client.get("/docs")
        assert res.status_code == 200
        res = client.get("/openapi.json")
        assert res.status_code == 200
    get_settings.cache_clear()


def test_docs_disabled_in_production(monkeypatch):
    from app.config import get_settings
    get_settings.cache_clear()
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("ENVIRONMENT", "production")
    prod_app = create_app()
    with TestClient(prod_app) as client:
        # In FastAPI, setting docs_url=None results in 404
        res_docs = client.get("/docs")
        assert res_docs.status_code == 404

        res_redoc = client.get("/redoc")
        assert res_redoc.status_code == 404

        res_openapi = client.get("/openapi.json")
        assert res_openapi.status_code == 404
    get_settings.cache_clear()


def test_security_headers_present():
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"
        assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        csp = response.headers.get("content-security-policy", "")
        assert "default-src 'self'" in csp
        assert "https://cdn.tailwindcss.com" in csp
        assert "https://fonts.googleapis.com" in csp


def test_static_cache_headers():
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/static/css/custom.css")
        assert response.status_code == 200
        cache_control = response.headers.get("cache-control", "")
        assert "public" in cache_control
        assert "max-age=31536000" in cache_control


def test_gzip_compression_on_large_payload():
    app = create_app()
    with TestClient(app) as client:
        # Request with gzip accept-encoding
        headers = {"Accept-Encoding": "gzip"}
        response = client.get("/", headers=headers)
        assert response.status_code == 200
        # HTML is > 1000 bytes, so it should be compressed
        assert response.headers.get("content-encoding") == "gzip"


def test_trusted_proxy_ip_spoofing_prevented(monkeypatch):
    """
    Verify that spoofed X-Forwarded-For headers (e.g. '1.1.1.1, 203.0.113.195')
    use the rightmost trusted proxy IP rather than the client-injected spoofed IP.
    """
    from app.config import get_settings
    from app.core.rate_limit import RateLimiter
    import app.core.rate_limit as rl_module
    from app.routes.chat import _client_ip
    from starlette.requests import Request

    settings = get_settings()
    monkeypatch.setattr(settings, "trusted_proxy_count", 1)

    # Simulated request: spoofed client prepended 1.1.1.1, proxy appended actual client IP 198.51.100.2
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/chat",
        "headers": [(b"x-forwarded-for", b"1.1.1.1, 198.51.100.2")],
        "client": ("10.0.0.1", 12345),
    }
    req = Request(scope)
    detected_ip = _client_ip(req)
    assert detected_ip == "198.51.100.2", f"Expected rightmost trusted IP, got {detected_ip}"

    # Rate limiting on detected_ip:
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    assert limiter.is_allowed(detected_ip) is True
    assert limiter.is_allowed(detected_ip) is True
    assert limiter.is_allowed(detected_ip) is False
    # A different IP should still be allowed
    assert limiter.is_allowed("198.51.100.3") is True


def test_health_reports_direct_mode_without_google_key(monkeypatch):
    """
    Verify that without GOOGLE_API_KEY, the app starts cleanly and /api/health reports direct mode.
    """
    from app.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "google_api_key", "")
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["rag_mode"] == "direct"
        assert data["mode"] == "direct"
