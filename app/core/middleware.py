"""
Security and caching middleware for production readiness.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies security headers to all responses:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - Referrer-Policy: strict-origin-when-cross-origin
    - Content-Security-Policy: permissive for Tailwind CDN, Google Fonts, and internal APIs
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Basic security hardening headers
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")

        # Content-Security-Policy allowing Tailwind CDN, Google Fonts, inline scripts/styles needed by theme
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers.setdefault("Content-Security-Policy", csp)

        return response


class StaticCacheMiddleware(BaseHTTPMiddleware):
    """
    Sets long-cache headers (Cache-Control: public, max-age=31536000, immutable)
    on successful GET requests to static assets (/static/).
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        if (
            request.method == "GET"
            and request.url.path.startswith("/static/")
            and response.status_code == 200
        ):
            # Avoid clobbering existing custom cache control if set
            if "Cache-Control" not in response.headers:
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response
