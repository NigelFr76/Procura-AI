"""Evaluation run and vendor score breakdown models."""

import enum
import uuid
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from app.models.procurement_request import ProcurementRequest
    from app.models.vendor import Vendor
    from app.models.scoring_policy import ScoringPolicy
    from app.models.compliance import ComplianceCheck
    from app.models.risk import RiskAssessment
    from app.models.scenario import ScenarioEvaluation
    from app.models.approval import ApprovalRecord


class EvaluationStatus(str, enum.Enum):
    """Evaluation lifecycle state."""
    INTAKE = "INTAKE"
    EVALUATING = "EVALUATING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class Evaluation(Base, TimestampMixin, TenantMixin):
    """Immutable evaluation run and baseline recommendation record."""

    __tablename__ = "evaluations"

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
    request_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("procurement_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scoring_policy_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("scoring_policies.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[EvaluationStatus] = mapped_column(
        Enum(EvaluationStatus, native_enum=False),
        default=EvaluationStatus.INTAKE,
        nullable=False,
        index=True,
    )
    thread_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    recommended_vendor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("vendors.id", ondelete="SET NULL"),
        nullable=True,
    )
    input_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 fingerprint of input snapshots guaranteeing reproducibility",
    )
    
    # Immutable Snapshots
    spec_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    policy_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    score_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    evidence_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    decision_explanation_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_immutable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    request: Mapped["ProcurementRequest"] = relationship("ProcurementRequest", back_populates="evaluations")
    scoring_policy: Mapped["ScoringPolicy"] = relationship("ScoringPolicy", lazy="selectin")
    recommended_vendor: Mapped[Optional["Vendor"]] = relationship("Vendor", lazy="selectin")
    scores: Mapped[List["VendorScore"]] = relationship(
        "VendorScore",
        back_populates="evaluation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    compliance_checks: Mapped[List["ComplianceCheck"]] = relationship(
        "ComplianceCheck",
        back_populates="evaluation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    risk_assessments: Mapped[List["RiskAssessment"]] = relationship(
        "RiskAssessment",
        back_populates="evaluation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    scenarios: Mapped[List["ScenarioEvaluation"]] = relationship(
        "ScenarioEvaluation",
        back_populates="baseline_evaluation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    approval_records: Mapped[List["ApprovalRecord"]] = relationship(
        "ApprovalRecord",
        back_populates="evaluation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class VendorScore(Base, TimestampMixin):
    """Detailed score card and ranking for a shortlisted vendor in an evaluation."""

    __tablename__ = "vendor_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
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
    is_eligible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ineligibility_reasons: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Normalized & Weighted Scores [0.0000 - 100.0000]
    overall_score: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    landed_cost_score: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    quality_score: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    delivery_score: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    compliance_score: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    risk_score: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    terms_score: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    
    # Authoritative Values
    landed_cost_calculated: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    confidence_penalty: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal("0.0000"), nullable=False)
    criterion_breakdowns: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    evaluation: Mapped["Evaluation"] = relationship("Evaluation", back_populates="scores")
    vendor: Mapped["Vendor"] = relationship("Vendor")
