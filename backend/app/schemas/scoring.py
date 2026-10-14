"""Pydantic schemas for deterministic vendor scoring, eligibility evaluation, and scorecards."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class VendorQuotationInput(BaseModel):
    """Normalized commercial inputs for scoring."""
    vendor_id: uuid.UUID
    vendor_name: str
    base_price: Decimal = Field(..., ge=0)
    freight_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    insurance_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    quoted_delivery_date: date
    incoterms: str = Field(default="DDP")
    payment_terms: str = Field(default="Net 30")
    warranty_months: int = Field(default=12, ge=0)


class VendorPerformanceInput(BaseModel):
    """Historical supplier performance metrics."""
    vendor_id: uuid.UUID
    defect_rate: Decimal = Field(default=Decimal("0.0000"), ge=0, le=1)
    on_time_delivery_rate: Decimal = Field(default=Decimal("1.0000"), ge=0, le=1)
    historical_orders_count: int = Field(default=0, ge=0)


class VendorComplianceInput(BaseModel):
    """Compliance verification metrics."""
    vendor_id: uuid.UUID
    certifications_held: List[str] = Field(default_factory=list)
    passed_mandatory_checks: int = Field(default=0, ge=0)
    total_mandatory_checks: int = Field(default=0, ge=0)
    passed_optional_checks: int = Field(default=0, ge=0)
    total_optional_checks: int = Field(default=0, ge=0)
    has_unverified_mandatory: bool = False


class VendorRiskInput(BaseModel):
    """Risk indicators for a shortlisted vendor."""
    vendor_id: uuid.UUID
    composite_risk_score: Decimal = Field(default=Decimal("0.00"), ge=0, le=100) # 0 is lowest risk, 100 is highest
    uncertainty_score: Decimal = Field(default=Decimal("0.0000"), ge=0, le=1)


class ProcurementRequirementsInput(BaseModel):
    """Procurement constraints and target objectives."""
    request_id: uuid.UUID
    budget_ceiling: Decimal = Field(..., gt=0)
    target_delivery_date: date
    max_acceptable_delivery_date: Optional[date] = None
    required_certifications: List[str] = Field(default_factory=list)
    currency: str = Field(default="USD", min_length=3, max_length=3)

    @model_validator(mode="after")
    def validate_dates(self) -> "ProcurementRequirementsInput":
        if self.max_acceptable_delivery_date and self.max_acceptable_delivery_date < self.target_delivery_date:
            raise ValueError("max_acceptable_delivery_date cannot be earlier than target_delivery_date")
        return self


class ScoringPolicyConfig(BaseModel):
    """Configurable weights and rules for multi-criteria scoring."""
    policy_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str = "Standard Procurement Policy"
    version: int = 1
    
    # Weights must sum to 1.0000
    cost_weight: Decimal = Field(default=Decimal("0.3000"), ge=0, le=1)
    quality_weight: Decimal = Field(default=Decimal("0.2000"), ge=0, le=1)
    delivery_weight: Decimal = Field(default=Decimal("0.2000"), ge=0, le=1)
    compliance_weight: Decimal = Field(default=Decimal("0.1500"), ge=0, le=1)
    risk_weight: Decimal = Field(default=Decimal("0.1000"), ge=0, le=1)
    terms_weight: Decimal = Field(default=Decimal("0.0500"), ge=0, le=1)

    tie_breaker_hierarchy: List[str] = Field(
        default_factory=lambda: ["quality_score", "risk_score", "landed_cost"]
    )

    @model_validator(mode="after")
    def validate_weights_sum(self) -> "ScoringPolicyConfig":
        total_weight = (
            self.cost_weight
            + self.quality_weight
            + self.delivery_weight
            + self.compliance_weight
            + self.risk_weight
            + self.terms_weight
        )
        if abs(total_weight - Decimal("1.0000")) > Decimal("0.0001"):
            raise ValueError(f"Scoring policy weights must sum to exactly 1.0000. Got: {total_weight}")
        return self


class VendorScoreDetail(BaseModel):
    """Detailed score breakdown and rank for a single vendor."""
    vendor_id: uuid.UUID
    vendor_name: str
    is_eligible: bool
    ineligibility_reasons: List[str] = Field(default_factory=list)
    
    # Financial result
    landed_cost_calculated: Decimal
    
    # Criteria Scores [0.0000 - 100.0000]
    landed_cost_score: Decimal
    quality_score: Decimal
    delivery_score: Decimal
    compliance_score: Decimal
    risk_score: Decimal
    terms_score: Decimal
    
    # Confidence Penalty applied for missing non-mandatory data
    confidence_penalty: Decimal = Decimal("0.0000")
    
    # Final Weighted Score [0.0000 - 100.0000]
    overall_score: Decimal
    rank: int
    
    criterion_breakdowns: Dict[str, Any] = Field(default_factory=dict)


class EvaluationScorecard(BaseModel):
    """Complete evaluation outcome with rankings and cryptographic fingerprint."""
    evaluation_id: uuid.UUID
    request_id: uuid.UUID
    policy_id: uuid.UUID
    recommended_vendor_id: Optional[uuid.UUID] = None
    recommended_vendor_name: Optional[str] = None
    scores: List[VendorScoreDetail]
    input_hash: str
    scoring_version: str = "1.0.0"
