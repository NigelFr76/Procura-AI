"""Supplier quotation and extracted commercial line items."""

import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from app.models.procurement_request import ProcurementRequest
    from app.models.vendor import Vendor
    from app.models.document import Document


class Quotation(Base, TimestampMixin, TenantMixin):
    """Normalized commercial quotation submitted by a vendor."""

    __tablename__ = "quotations"

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
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("vendors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    quote_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    # Financial components for deterministic landed cost calculation
    base_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    freight_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)
    insurance_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)
    total_quote_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    # Commercial Terms
    quoted_delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    validity_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    incoterms: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    payment_terms: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    warranty_months: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    
    # Extraction & Provenance
    is_normalized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_extraction_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    request: Mapped["ProcurementRequest"] = relationship("ProcurementRequest", back_populates="quotations", lazy="selectin")
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="quotations", lazy="selectin")
    document: Mapped[Optional["Document"]] = relationship("Document", back_populates="quotation", lazy="selectin")
    items: Mapped[List["QuotationLineItem"]] = relationship(
        "QuotationLineItem",
        back_populates="quotation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class QuotationLineItem(Base, TimestampMixin):
    """Extracted item-level quotation price and specifications."""

    __tablename__ = "quotation_line_items"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    quotation_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    lead_time_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    evidence_location: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    quotation: Mapped["Quotation"] = relationship("Quotation", back_populates="items")
