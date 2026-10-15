"""Enterprise security headers and rate-limiting middleware for production hardening."""

import time
from typing import Callable, Dict, Tuple
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforce strict production HTTP response security headers."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        return response


class InMemoryRateLimiter:
    """Sliding-window token bucket rate limiter to prevent API abuse and DoS."""

    def __init__(self, requests_per_minute: int = 120):
        self.rate = requests_per_minute
        self.window_seconds = 60
        # client_key -> list of request timestamps
        self.records: Dict[str, list[float]] = {}

    def is_rate_limited(self, client_key: str) -> Tuple[bool, int]:
        """Check if client exceeds permitted threshold. Returns (is_limited, retry_after)."""
        now = time.time()
        window_start = now - self.window_seconds

        if client_key not in self.records:
            self.records[client_key] = [now]
            return False, 0

        # Filter out expired requests
        valid_requests = [ts for ts in self.records[client_key] if ts > window_start]
        self.records[client_key] = valid_requests

        if len(valid_requests) >= self.rate:
            oldest = valid_requests[0]
            retry_after = int(self.window_seconds - (now - oldest)) + 1
            return True, max(1, retry_after)

        self.records[client_key].append(now)
        return False, 0


rate_limiter = InMemoryRateLimiter(requests_per_minute=300)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate-limiting middleware intercepting unauthenticated or burst requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Exempt health and docs endpoints
        path = request.url.path
        if path in {"/", "/api/v1/health", "/api/v1/docs", "/api/v1/openapi.json", "/api/v1/redoc"}:
            return await call_next(request)

        # Extract client identifier: tenant or remote IP
        client_ip = request.client.host if request.client else "unknown"
        tenant_header = request.headers.get("X-Tenant-ID", client_ip)
        client_key = f"{tenant_header}:{client_ip}"

        is_limited, retry_after = rate_limiter.is_rate_limited(client_key)
        if is_limited:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit threshold exceeded. Please slow down your requests.",
                    "retry_after_seconds": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
