"""State definitions for the LangGraph multi-agent procurement workflow."""

from typing import Any, Dict, List, Optional, TypedDict


class ProcurementEvaluationState(TypedDict, total=False):
    """Authoritative state shared across all LangGraph procurement evaluation nodes."""
    
    # Organization and Tenancy Identifiers
    organization_id: str
    request_id: str
    evaluation_id: str
    thread_id: str
    
    # Workflow Execution Status
    status: str  # INTAKE, DISCOVERY, EVALUATING, AWAITING_CLARIFICATION, AWAITING_APPROVAL, APPROVED, REJECTED
    is_clarification_needed: bool
    clarification_questions: List[str]
    missing_fields: List[str]

    # Phase 1: Intake & Specs (Agent 1)
    raw_input: Dict[str, Any]
    spec_result: Dict[str, Any]
    procurement_spec: Dict[str, Any]

    # Phase 2: Vendor Discovery (Agent 2)
    shortlisted_vendors: List[Dict[str, Any]]
    excluded_vendors: List[Dict[str, Any]]

    # Phase 3: Quotation Extraction (Agent 3)
    quotations: List[Dict[str, Any]]

    # Phase 4: Compliance & Risk (Agents 4 & 5)
    compliance_rules: List[Dict[str, Any]]
    compliance_results: List[Dict[str, Any]]
    risk_results: List[Dict[str, Any]]

    # Phase 5: Scoring Engine (Deterministic Scoring Service)
    scoring_policy: Dict[str, Any]
    scorecard: Dict[str, Any]

    # Phase 6: Decision Explanation (Agent 8)
    decision_explanation: Dict[str, Any]

    # Phase 7: Human Approval Gate (HITL)
    approval_status: str  # PENDING, APPROVED, REJECTED, MODIFICATION_REQUESTED
    approval_action: Optional[str]
    approval_comments: Optional[str]
    approver_user_id: Optional[str]
    signature_hash: Optional[str]
    decided_at: Optional[str]

    # Error Handling & Auditing
    error_message: Optional[str]
