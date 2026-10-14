"""Scoring policy models and weight versioning."""

import uuid
from decimal import Decimal
from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, TimestampMixin, TenantMixin


class ScoringPolicy(Base, TimestampMixin, TenantMixin):
    """Configurable scoring criteria weights and normalization policy."""

    __tablename__ = "scoring_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Configurable criterion weights (sum must equal 1.0000)
    cost_weight: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.3000"), nullable=False)
    quality_weight: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.2000"), nullable=False)
    delivery_weight: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.2000"), nullable=False)
    compliance_weight: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.1500"), nullable=False)
    risk_weight: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.1000"), nullable=False)
    terms_weight: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0500"), nullable=False)

    # Deterministic Evaluation Settings
    tie_breaker_rules: Mapped[list] = mapped_column(
        JSON,
        default=lambda: ["quality_score", "risk_score", "landed_cost"],
        nullable=False,
    )
    normalization_rules: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
