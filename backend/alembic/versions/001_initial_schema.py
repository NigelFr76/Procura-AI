"""Initial database schema migration for AI Procurement Platform.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-14 23:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from app.models import Base

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable postgres extensions if on postgresql
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')
        op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
        op.execute('CREATE SCHEMA IF NOT EXISTS checkpoints')

    # Create all domain model tables
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
