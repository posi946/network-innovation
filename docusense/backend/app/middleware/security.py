"""Security headers, audit logging and CSP nonce middleware (Days 3–4)."""
from __future__ import annotations

import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..core.sanitizer import generate_csp_nonce, strip_response_header_injection


class SecurityAndLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        nonce = generate_csp_nonce()
        request.state.csp_nonce = nonce
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(self), camera=(self)"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}'; "
            "style-src 'self' fonts.googleapis.com 'unsafe-inline'; "
            "connect-src 'self' *.supabase.co"
        )
        response.headers["X-Response-Time-Ms"] = strip_response_header_injection(str(duration_ms))

        user = getattr(request.state, "user", None)
        if user is not None:
            try:
                from ..models.database import log_audit
                log_audit(
                    user_id=getattr(user, "id", None),
                    action=f"{request.method} {request.url.path}",
                    ip=request.headers.get("x-forwarded-for", request.client.host if request.client else ""),
                    user_agent=request.headers.get("user-agent", ""),
                    endpoint=request.url.path,
                    method=request.method,
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                )
            except Exception:
                pass  # auditing must never break the request
        return response
