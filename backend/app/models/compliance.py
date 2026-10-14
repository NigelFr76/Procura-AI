"""Compliance rules and vendor compliance verification records."""

import enum
import uuid
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Boolean, Enum, ForeignKey, Numeric, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from app.models.vendor import Vendor
    from app.models.document import Document
    from app.models.evaluation import Evaluation


class ComplianceRuleType(str, enum.Enum):
    """Execution type for compliance rules."""
    DETERMINISTIC_THRESHOLD = "DETERMINISTIC_THRESHOLD"
    CERTIFICATION_REQUIRED = "CERTIFICATION_REQUIRED"
    CONTRACTUAL_CLAUSE = "CONTRACTUAL_CLAUSE"


class ComplianceStatus(str, enum.Enum):
    """Deterministic or verified compliance outcome."""
    PASS = "PASS"
    FAIL = "FAIL"
    UNVERIFIED = "UNVERIFIED"


class ComplianceRule(Base, TimestampMixin, TenantMixin):
    """Organization procurement policy or compliance requirement."""

    __tablename__ = "compliance_rules"

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
    rule_code: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rule_type: Mapped[ComplianceRuleType] = mapped_column(
        Enum(ComplianceRuleType, native_enum=False),
        default=ComplianceRuleType.CERTIFICATION_REQUIRED,
        nullable=False,
    )
    parameters: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class ComplianceCheck(Base, TimestampMixin, TenantMixin):
    """Evidence-linked verification result for an individual vendor under evaluation."""

    __tablename__ = "compliance_checks"

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
    rule_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("compliance_rules.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[ComplianceStatus] = mapped_column(
        Enum(ComplianceStatus, native_enum=False),
        default=ComplianceStatus.UNVERIFIED,
        nullable=False,
    )
    confidence_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("1.0000"),
        nullable=False,
    )
    evidence_quote: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    evidence_location: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    rule: Mapped["ComplianceRule"] = relationship("ComplianceRule")
    vendor: Mapped["Vendor"] = relationship("Vendor")
    evaluation: Mapped["Evaluation"] = relationship("Evaluation", back_populates="compliance_checks")
