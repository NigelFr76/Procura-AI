"""Risk assessment models and supplier risk telemetry."""

import enum
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import Enum, ForeignKey, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from app.models.vendor import Vendor
    from app.models.evaluation import Evaluation


class RiskTier(str, enum.Enum):
    """Aggregate risk classification."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskAssessment(Base, TimestampMixin, TenantMixin):
    """Comprehensive risk profile for a vendor in an active procurement evaluation."""

    __tablename__ = "risk_assessments"

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
    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("evaluations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("vendors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    composite_risk_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Inverted composite risk factor [0.00 - 100.00]",
    )
    risk_tier: Mapped[RiskTier] = mapped_column(
        Enum(RiskTier, native_enum=False),
        default=RiskTier.LOW,
        nullable=False,
    )
    delivery_risk: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    quality_risk: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    financial_risk: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    concentration_risk: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    geopolitical_risk: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    uncertainty_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False,
        comment="Confidence penalty due to sparse historical records [0.0000 - 1.0000]",
    )
    risk_factors: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    mitigation_recommendations: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # Relationships
    vendor: Mapped["Vendor"] = relationship("Vendor")
    evaluation: Mapped["Evaluation"] = relationship("Evaluation", back_populates="risk_assessments")
