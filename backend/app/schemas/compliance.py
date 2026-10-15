"""Schemas for compliance rule evaluation and evidence-grounded checks."""

import uuid
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.compliance import ComplianceStatus, ComplianceRuleType
from app.schemas.quotation_extraction import EvidenceLocation


class RuleCheckDetail(BaseModel):
    """Detailed verification result for a single compliance rule."""
    rule_id: uuid.UUID
    rule_code: str
    rule_name: str
    rule_type: ComplianceRuleType
    is_mandatory: bool
    status: ComplianceStatus
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence_quote: Optional[str] = None
    evidence_location: Optional[EvidenceLocation] = None
    explanation: str


class ComplianceRuleInput(BaseModel):
    """Specification of an organization policy rule to be evaluated."""
    rule_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    rule_code: str
    rule_name: str
    rule_type: ComplianceRuleType
    is_mandatory: bool = True
    parameters: dict = Field(default_factory=dict)


class ComplianceInput(BaseModel):
    """Inputs supplied to Agent 4 to evaluate vendor compliance."""
    vendor_id: uuid.UUID
    vendor_name: str
    rules: List[ComplianceRuleInput]
    held_certifications: List[str] = Field(default_factory=list)
    quotation_terms: Optional[dict] = Field(default_factory=dict)
    evidence_text_chunks: List[str] = Field(default_factory=list)


class ComplianceResult(BaseModel):
    """Aggregate compliance verification outcome for a vendor."""
    vendor_id: uuid.UUID
    overall_status: ComplianceStatus
    has_unverified_mandatory: bool = False
    passed_mandatory_checks: int = 0
    total_mandatory_checks: int = 0
    passed_optional_checks: int = 0
    total_optional_checks: int = 0
    checks: List[RuleCheckDetail] = Field(default_factory=list)
