"""Schemas for Agent 8: Decision Explanation Agent."""

import uuid
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.scoring import EvaluationScorecard, ScoringPolicyConfig
from app.schemas.compliance import ComplianceResult
from app.schemas.risk import RiskAssessmentResult


class DecisionExplanationInput(BaseModel):
    """Input parameters passed to Agent 8 to synthesize narrative audit justification."""
    evaluation_id: uuid.UUID
    scorecard: EvaluationScorecard
    compliance_results: List[ComplianceResult] = Field(default_factory=list)
    risk_results: List[RiskAssessmentResult] = Field(default_factory=list)
    policy_config: ScoringPolicyConfig


class DecisionExplanationResult(BaseModel):
    """Audit-ready narrative explanation verified against authoritative scorecards."""
    evaluation_id: uuid.UUID
    recommended_vendor_id: Optional[uuid.UUID] = None
    recommended_vendor_name: Optional[str] = None
    executive_summary: str
    winner_justification: str
    runner_up_comparison: str
    key_tradeoffs: List[str] = Field(default_factory=list)
    risk_and_compliance_summary: str
    recommended_actions: List[str] = Field(default_factory=list)
    verification_passed: bool = True
    audit_warnings: List[str] = Field(default_factory=list)
