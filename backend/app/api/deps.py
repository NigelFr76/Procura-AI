"""FastAPI dependency injection utilities for DB sessions, tenant isolation, and auth."""

import uuid
from typing import AsyncGenerator
from fastapi import Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory, set_current_tenant

DEFAULT_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEFAULT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency providing an isolated async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_tenant_id(
    x_organization_id: str = Header(
        default=str(DEFAULT_ORG_ID),
        description="Tenant organization UUID header",
    )
) -> uuid.UUID:
    """Extract and validate tenant organization ID from request header."""
    try:
        org_id = uuid.UUID(x_organization_id)
        set_current_tenant(org_id)
        return org_id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Organization-Id header format. Must be a valid UUID.",
        )


def get_current_user_id(
    x_user_id: str = Header(
        default=str(DEFAULT_USER_ID),
        description="Active authenticated user UUID header",
    )
) -> uuid.UUID:
    """Extract authenticated user ID from request header."""
    try:
        return uuid.UUID(x_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-User-Id header format. Must be a valid UUID.",
        )
