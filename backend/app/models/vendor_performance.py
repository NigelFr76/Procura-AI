"""Historical vendor performance records and operational metrics."""

import uuid
from datetime import date
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import Date, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from app.models.vendor import Vendor


class VendorPerformanceHistory(Base, TimestampMixin, TenantMixin):
    """Historical delivery reliability and quality tracking."""

    __tablename__ = "vendor_performance_history"

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
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("vendors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    defect_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False,
        comment="Ratio of defective units [0.0000 - 1.0000]",
    )
    on_time_delivery_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("1.0000"),
        nullable=False,
        comment="Ratio of on-time shipments [0.0000 - 1.0000]",
    )
    average_response_time_hours: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )
    historical_orders_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_spend: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    audit_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="performance_records")
