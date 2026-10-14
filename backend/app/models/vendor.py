"""Vendor entity and profile definitions."""

import enum
import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Enum, ForeignKey, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin, TenantMixin, VectorType

if TYPE_CHECKING:
    from app.models.vendor_performance import VendorPerformanceHistory
    from app.models.quotation import Quotation


class VendorStatus(str, enum.Enum):
    """Vendor lifecycle verification status."""
    UNVERIFIED = "UNVERIFIED"
    SHORTLISTED = "SHORTLISTED"
    VERIFIED = "VERIFIED"
    SUSPENDED = "SUSPENDED"


class Vendor(Base, TimestampMixin, TenantMixin):
    """Supplier registry entity."""

    __tablename__ = "vendors"

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
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    tax_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    registration_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="US", nullable=False)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[VendorStatus] = mapped_column(
        Enum(VendorStatus, native_enum=False),
        default=VendorStatus.UNVERIFIED,
        nullable=False,
    )
    metadata_info: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    profile_vector: Mapped[Optional[list]] = mapped_column(VectorType(1536), nullable=True)

    # Relationships
    performance_records: Mapped[List["VendorPerformanceHistory"]] = relationship(
        "VendorPerformanceHistory",
        back_populates="vendor",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    quotations: Mapped[List["Quotation"]] = relationship(
        "Quotation",
        back_populates="vendor",
    )
