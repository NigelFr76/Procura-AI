"""Schemas for What-If scenario simulation and differential analysis."""

import uuid
from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.scoring import (
    EvaluationScorecard,
    ProcurementRequirementsInput,
    ScoringPolicyConfig,
    VendorComplianceInput,
    VendorPerformanceInput,
    VendorQuotationInput,
    VendorRiskInput,
)


class ScenarioParameterOverrides(BaseModel):
    """Hypothetical overrides applied to a deep copy of a baseline evaluation."""
    # Policy weight adjustments (must still sum to 1.0 if provided)
    policy_weight_overrides: Optional[Dict[str, Decimal]] = None
    
    # Vendor-specific commercial/operational overrides
    vendor_price_overrides: Optional[Dict[uuid.UUID, Decimal]] = None
    vendor_delivery_overrides: Optional[Dict[uuid.UUID, str]] = None  # YYYY-MM-DD or date
    vendor_cert_revocations: Optional[Dict[uuid.UUID, List[str]]] = None
    
    # Requirement constraints override
    budget_ceiling_override: Optional[Decimal] = None


class VendorDifferential(BaseModel):
    """Quantified delta between baseline evaluation and scenario outcome for a single supplier."""
    vendor_id: uuid.UUID
    vendor_name: str
    baseline_rank: int
    scenario_rank: int
    rank_delta: int = Field(..., description="Positive indicates improvement, negative indicates drop")
    baseline_score: Decimal
    scenario_score: Decimal
    score_delta: Decimal
    baseline_landed_cost: Decimal
    scenario_landed_cost: Decimal
    cost_delta: Decimal
    baseline_eligible: bool
    scenario_eligible: bool
    eligibility_shifted: bool = False


class ScenarioRunInput(BaseModel):
    """Complete specification to execute a What-If scenario simulation."""
    scenario_name: str
    scenario_description: Optional[str] = None
    baseline_evaluation_id: uuid.UUID
    baseline_requirements: ProcurementRequirementsInput
    baseline_quotes: List[VendorQuotationInput]
    baseline_performances: Dict[uuid.UUID, VendorPerformanceInput]
    baseline_compliances: Dict[uuid.UUID, VendorComplianceInput]
    baseline_risks: Dict[uuid.UUID, VendorRiskInput]
    baseline_policy: ScoringPolicyConfig
    baseline_scorecard: EvaluationScorecard
    overrides: ScenarioParameterOverrides = Field(default_factory=ScenarioParameterOverrides)


class ScenarioRunResult(BaseModel):
    """Authoritative output of a What-If simulation with differential analysis and causal explanation."""
    scenario_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    scenario_name: str
    baseline_evaluation_id: uuid.UUID
    baseline_input_hash: str
    baseline_immutable_verified: bool = True
    winner_displaced: bool = False
    previous_winner_id: Optional[uuid.UUID] = None
    previous_winner_name: Optional[str] = None
    new_winner_id: Optional[uuid.UUID] = None
    new_winner_name: Optional[str] = None
    vendor_differentials: List[VendorDifferential] = Field(default_factory=list)
    causal_explanation: str
    scenario_scorecard: EvaluationScorecard
