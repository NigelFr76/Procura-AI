"""What-If scenario simulation entity and differential analysis."""

import enum
import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Boolean, Enum, ForeignKey, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from app.models.evaluation import Evaluation
    from app.models.vendor import Vendor


class ScenarioStatus(str, enum.Enum):
    """Scenario execution status."""
    PENDING = "PENDING"
    COMPUTED = "COMPUTED"
    FAILED = "FAILED"


class ScenarioEvaluation(Base, TimestampMixin, TenantMixin):
    """Hypothetical simulation forked from an immutable baseline evaluation."""

    __tablename__ = "scenario_evaluations"

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
    baseline_evaluation_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("evaluations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Hypothetical Parameter Shift
    parameters_delta: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Structured overrides e.g. price shifts, delivery delays, revoked certs",
    )
    status: Mapped[ScenarioStatus] = mapped_column(
        Enum(ScenarioStatus, native_enum=False),
        default=ScenarioStatus.PENDING,
        nullable=False,
    )
    
    # Differential Analysis Results
    score_deltas: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    rank_shifts: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    winner_displaced: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    previous_winner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("vendors.id", ondelete="SET NULL"),
        nullable=True,
    )
    new_winner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("vendors.id", ondelete="SET NULL"),
        nullable=True,
    )
    causal_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scenario_scores_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    baseline_evaluation: Mapped["Evaluation"] = relationship(
        "Evaluation",
        back_populates="scenarios",
    )
    previous_winner: Mapped[Optional["Vendor"]] = relationship("Vendor", foreign_keys=[previous_winner_id])
    new_winner: Mapped[Optional["Vendor"]] = relationship("Vendor", foreign_keys=[new_winner_id])
