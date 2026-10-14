"""Human-in-the-loop procurement approval sign-off records."""

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from app.models.evaluation import Evaluation
    from app.models.user import User


class ApprovalAction(str, enum.Enum):
    """Authorized officer approval decision."""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MODIFICATION_REQUESTED = "MODIFICATION_REQUESTED"


class ApprovalRecord(Base, TimestampMixin, TenantMixin):
    """Tamper-evident human approval gate record."""

    __tablename__ = "approval_records"

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
    approver_user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    action: Mapped[ApprovalAction] = mapped_column(
        Enum(ApprovalAction, native_enum=False),
        nullable=False,
    )
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    signature_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="Cryptographic SHA-256 binding approver, timestamp, and evaluation snapshot",
    )
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    evaluation: Mapped["Evaluation"] = relationship("Evaluation", back_populates="approval_records")
    approver: Mapped["User"] = relationship("User")
