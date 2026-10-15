"""Schemas for quantitative and qualitative risk assessments."""

import uuid
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.risk import RiskTier


class RiskFactorDetail(BaseModel):
    """Specific risk factor telemetry identified for a vendor."""
    category: str = Field(..., description="DELIVERY, QUALITY, FINANCIAL, CONCENTRATION, or GEOPOLITICAL")
    severity: RiskTier
    score: float = Field(..., ge=0.0, le=100.0, description="0 is lowest risk, 100 is highest risk")
    description: str
    mitigation_suggestion: str


class RiskInput(BaseModel):
    """Telemetry and operational records passed to Agent 5 for risk profiling."""
    vendor_id: uuid.UUID
    vendor_name: str
    defect_rate: Decimal = Field(default=Decimal("0.0000"), ge=0, le=1)
    on_time_delivery_rate: Decimal = Field(default=Decimal("1.0000"), ge=0, le=1)
    historical_orders_count: int = Field(default=0, ge=0)
    spend_concentration_pct: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    country: Optional[str] = "USA"
    sanction_flag: bool = False
    qualitative_notes: Optional[str] = None


class RiskAssessmentResult(BaseModel):
    """Comprehensive multi-dimensional risk assessment for a shortlisted vendor."""
    vendor_id: uuid.UUID
    composite_risk_score: Decimal = Field(..., ge=0, le=100)
    risk_tier: RiskTier
    delivery_risk: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    quality_risk: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    financial_risk: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    concentration_risk: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    geopolitical_risk: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    uncertainty_score: Decimal = Field(default=Decimal("0.0000"), ge=0, le=1)
    factors: List[RiskFactorDetail] = Field(default_factory=list)
    mitigations: List[str] = Field(default_factory=list)
