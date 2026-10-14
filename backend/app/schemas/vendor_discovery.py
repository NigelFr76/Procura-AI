"""Schemas for Vendor Discovery Agent shortlisting and audit trail."""

import uuid
from typing import List
from pydantic import BaseModel, Field
from app.schemas.spec import ProcurementSpecification


class VendorDiscoveryInput(BaseModel):
    """Input payload for Vendor Discovery Agent."""
    spec: ProcurementSpecification
    organization_id: uuid.UUID
    max_shortlist: int = Field(default=5, ge=1, le=20)


class ShortlistedVendor(BaseModel):
    """Supplier selected for detailed quotation and compliance evaluation."""
    vendor_id: uuid.UUID
    vendor_name: str
    country: str
    status: str
    match_score: float = Field(..., ge=0.0, le=1.0)
    match_reasons: List[str] = Field(default_factory=list)
    held_certifications: List[str] = Field(default_factory=list)
    is_verified: bool = False


class ExcludedVendor(BaseModel):
    """Supplier evaluated but excluded from the shortlist with documented justification."""
    vendor_id: uuid.UUID
    vendor_name: str
    exclusion_reasons: List[str] = Field(default_factory=list)


class VendorShortlistResult(BaseModel):
    """Outcome of vendor registry discovery search."""
    shortlisted: List[ShortlistedVendor] = Field(default_factory=list)
    excluded: List[ExcludedVendor] = Field(default_factory=list)
    total_registry_scanned: int = 0
    search_summary: str
