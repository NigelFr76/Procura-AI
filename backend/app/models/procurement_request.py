"""Procurement request and line item models."""

import enum
import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Date, Enum, ForeignKey, Numeric, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.document import Document
    from app.models.quotation import Quotation
    from app.models.evaluation import Evaluation


class RequestStatus(str, enum.Enum):
    """Procurement request lifecycle status."""
    DRAFT = "DRAFT"
    REQUIREMENT_CLARIFICATION = "REQUIREMENT_CLARIFICATION"
    UNDER_EVALUATION = "UNDER_EVALUATION"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class RequestPriority(str, enum.Enum):
    """Business urgency priority."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ProcurementRequest(Base, TimestampMixin, TenantMixin):
    """Procurement project or purchase requisition header."""

    __tablename__ = "procurement_requests"

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
    requester_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    budget_ceiling: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        comment="Maximum permissible total procurement budget",
    )
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    target_delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, native_enum=False),
        default=RequestStatus.DRAFT,
        nullable=False,
        index=True,
    )
    priority: Mapped[RequestPriority] = mapped_column(
        Enum(RequestPriority, native_enum=False),
        default=RequestPriority.MEDIUM,
        nullable=False,
    )
    spec_structured_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    requester: Mapped["User"] = relationship("User", lazy="selectin")
    items: Mapped[List["ProcurementRequestItem"]] = relationship(
        "ProcurementRequestItem",
        back_populates="request",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="request",
        cascade="all, delete-orphan",
    )
    quotations: Mapped[List["Quotation"]] = relationship(
        "Quotation",
        back_populates="request",
    )
    evaluations: Mapped[List["Evaluation"]] = relationship(
        "Evaluation",
        back_populates="request",
        cascade="all, delete-orphan",
    )


class ProcurementRequestItem(Base, TimestampMixin):
    """Specific line item or product required in procurement request."""

    __tablename__ = "procurement_request_items"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("procurement_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(50), default="units", nullable=False)
    target_unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    technical_specs: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    mandatory_certifications: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # Relationships
    request: Mapped["ProcurementRequest"] = relationship("ProcurementRequest", back_populates="items")
