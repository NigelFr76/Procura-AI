"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, Any
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import get_logger, setup_logging

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifespan management."""
    setup_logging(settings.LOG_LEVEL)
    logger.info("Starting up %s in %s environment...", settings.PROJECT_NAME, settings.ENVIRONMENT)
    try:
        yield
    finally:
        logger.info("Shutting down %s...", settings.PROJECT_NAME)


def create_application() -> FastAPI:
    """Application factory for FastAPI."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    # Set up CORS middleware
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Production Hardening: Security Headers & Rate Limiting
    from app.core.security import SecurityHeadersMiddleware, RateLimitMiddleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)

    @app.get("/", tags=["Root"])
    async def root_info() -> Dict[str, Any]:
        """Root API welcome & system information."""
        return {
            "name": settings.PROJECT_NAME,
            "version": "0.1.0",
            "environment": settings.ENVIRONMENT,
            "docs": f"{settings.API_V1_STR}/docs",
            "status": "operational",
        }

    @app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
    async def health_check() -> JSONResponse:
        """System health and operational status check."""
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service": "api",
                "environment": settings.ENVIRONMENT,
                "version": "0.1.0",
            },
        )

    # Mount v1 REST API routes
    from app.api.v1.api import api_router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()
