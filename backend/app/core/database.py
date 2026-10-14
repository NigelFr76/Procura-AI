"""Database session management, connection pooling, and multi-tenant scoping."""

import uuid
from contextvars import ContextVar
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.sql import Select

from app.core.config import settings

# Thread-safe ContextVar to store active organization ID for tenant isolation
current_tenant_id: ContextVar[Optional[uuid.UUID]] = ContextVar("current_tenant_id", default=None)


def set_current_tenant(organization_id: Optional[uuid.UUID]) -> None:
    """Set the active organization tenant context for the current request context."""
    current_tenant_id.set(organization_id)


def get_current_tenant() -> Optional[uuid.UUID]:
    """Retrieve the active organization tenant context."""
    return current_tenant_id.get()


# Engine configuration
engine_kwargs = {}
if "sqlite" not in settings.async_database_url:
    engine_kwargs.update({
        "pool_size": settings.POSTGRES_POOL_SIZE,
        "max_overflow": settings.POSTGRES_MAX_OVERFLOW,
        "pool_pre_ping": True,
    })

engine = create_async_engine(
    settings.async_database_url,
    **engine_kwargs,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def with_tenant_filter(statement: Select, model: type, tenant_id: Optional[uuid.UUID] = None) -> Select:
    """Enforce organization tenant isolation filter on queries."""
    active_id = tenant_id or get_current_tenant()
    if active_id and hasattr(model, "organization_id"):
        return statement.where(model.organization_id == active_id)
    return statement
