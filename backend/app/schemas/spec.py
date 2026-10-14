"""Schemas for requirement intake, specification extraction, and clarification loops."""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RawProcurementInput(BaseModel):
    """Raw natural language procurement request input by user."""
    text: str = Field(..., min_length=5, description="Free-text requirement description")
    budget_ceiling: Optional[Decimal] = Field(default=None, ge=0)
    target_delivery_date: Optional[date] = None
    currency: Optional[str] = Field(default="USD", min_length=3, max_length=3)
    required_certifications: Optional[List[str]] = Field(default_factory=list)


class ExtractedItemSpec(BaseModel):
    """Structured line item extracted from procurement requirement."""
    item_code: Optional[str] = None
    description: str = Field(..., min_length=2)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="units")
    target_unit_price: Optional[Decimal] = Field(default=None, ge=0)
    technical_specs: Dict[str, Any] = Field(default_factory=dict)


class ProcurementSpecification(BaseModel):
    """Validated structured procurement specification."""
    title: str = Field(..., min_length=3)
    description: str
    items: List[ExtractedItemSpec] = Field(default_factory=list)
    budget_ceiling: Optional[Decimal] = Field(default=None, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    target_delivery_date: Optional[date] = None
    required_certifications: List[str] = Field(default_factory=list)
    commercial_constraints: Dict[str, Any] = Field(default_factory=dict)


class ProcurementSpecResult(BaseModel):
    """Output from Requirement Analysis Agent indicating completeness or clarification needed."""
    spec: ProcurementSpecification
    is_complete: bool = Field(..., description="True if all mandatory fields and clear quantities exist")
    missing_fields: List[str] = Field(default_factory=list)
    clarification_questions: List[str] = Field(default_factory=list)
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
