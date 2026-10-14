"""Schemas for Quotation Analysis Agent document extraction and evidence linking."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class EvidenceLocation(BaseModel):
    """Exact source document citation with visual bounding box coordinates."""
    document_id: uuid.UUID
    page_number: int
    bbox: List[float] = Field(..., min_length=4, max_length=4, description="[x1, y1, x2, y2] normalized 0-1")
    text_snippet: str


class ExtractedQuotationItem(BaseModel):
    """Line item extracted from supplier document."""
    item_code: Optional[str] = None
    description: str
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    total_price: Decimal = Field(..., ge=0)
    evidence: Optional[EvidenceLocation] = None


class NormalizedQuotationResult(BaseModel):
    """Standardized commercial quotation extracted from PDF/spreadsheet."""
    document_id: uuid.UUID
    vendor_name: str
    quote_reference: Optional[str] = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    
    # Financial terms
    base_price: Decimal = Field(..., ge=0)
    freight_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    insurance_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_quote_amount: Decimal = Field(..., ge=0)
    
    # Delivery & Commercial Conditions
    quoted_delivery_date: date
    validity_end_date: Optional[date] = None
    incoterms: str = Field(default="DDP")
    payment_terms: str = Field(default="Net 30")
    warranty_months: int = Field(default=12, ge=0)
    
    line_items: List[ExtractedQuotationItem] = Field(default_factory=list)
    ambiguity_flags: List[str] = Field(
        default_factory=list,
        description="Explicit flags where terms were missing or ambiguous in document",
    )
    evidence_locations: Dict[str, EvidenceLocation] = Field(
        default_factory=dict,
        description="Mapping from field name (e.g. 'base_price', 'payment_terms') to source document evidence",
    )
