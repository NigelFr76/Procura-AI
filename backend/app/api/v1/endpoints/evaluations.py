"""FastAPI router for Multi-Agent evaluations and HITL approval workflow."""

import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user_id, get_tenant_id
from app.agents.coordinator_agent import coordinator
from app.core.events import broadcaster

router = APIRouter()


class StartEvaluationRequest(BaseModel):
    """Payload to trigger an end-to-end multi-agent procurement evaluation."""
    text: str
    budget_ceiling: Optional[Decimal] = None
    target_delivery_date: Optional[str] = None
    currency: str = "USD"
    required_certifications: List[str] = Field(default_factory=list)
    candidate_vendors: List[Dict[str, Any]] = Field(default_factory=list)
    compliance_rules: List[Dict[str, Any]] = Field(default_factory=list)
    quotations: List[Dict[str, Any]] = Field(default_factory=list)
    scoring_policy: Optional[Dict[str, Any]] = None
    thread_id: Optional[str] = None


class ApprovalDecisionRequest(BaseModel):
    """Payload for human procurement officer authorization sign-off."""
    action: str = Field(..., description="APPROVED, REJECTED, or MODIFICATION_REQUESTED")
    comments: str = Field(default="Reviewed and authorized.")


@router.post("", status_code=status.HTTP_201_CREATED)
async def start_evaluation(
    payload: StartEvaluationRequest,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Trigger the multi-agent procurement evaluation pipeline."""
    t_id = payload.thread_id or f"eval-{uuid.uuid4()}"

    await broadcaster.broadcast(
        channel=t_id,
        event_type="evaluation.started",
        payload={"thread_id": t_id, "status": "INTAKE"},
    )

    budget_val = float(payload.budget_ceiling) if payload.budget_ceiling else None

    state = coordinator.start_evaluation(
        raw_text=payload.text,
        organization_id=str(tenant_id),
        budget_ceiling=budget_val,
        target_delivery_date=payload.target_delivery_date,
        currency=payload.currency,
        required_certifications=payload.required_certifications,
        candidate_vendors=payload.candidate_vendors,
        compliance_rules=payload.compliance_rules,
        quotations=payload.quotations,
        scoring_policy=payload.scoring_policy,
        thread_id=t_id,
    )

    await broadcaster.broadcast(
        channel=t_id,
        event_type="evaluation.node_transition",
        payload={"thread_id": t_id, "status": state.get("status")},
    )

    return {
        "thread_id": t_id,
        "evaluation_id": state.get("evaluation_id"),
        "status": state.get("status"),
        "is_clarification_needed": state.get("is_clarification_needed", False),
        "clarification_questions": state.get("clarification_questions", []),
        "scorecard": state.get("scorecard"),
        "decision_explanation": state.get("decision_explanation"),
        "interrupt": state.get("__interrupt__"),
    }


@router.get("/{thread_id}")
async def get_evaluation_status(
    thread_id: str,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Retrieve current evaluation state and scorecard snapshot by thread ID."""
    state = coordinator.get_evaluation_state(thread_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation with thread_id '{thread_id}' was not found.",
        )
    return state


@router.post("/{thread_id}/approval")
async def submit_human_approval(
    thread_id: str,
    payload: ApprovalDecisionRequest,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Submit human officer sign-off to resume and finalize an interrupted evaluation."""
    valid_actions = {"APPROVED", "REJECTED", "MODIFICATION_REQUESTED"}
    if payload.action.upper() not in valid_actions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action '{payload.action}'. Must be one of {valid_actions}.",
        )

    resumed_state = coordinator.submit_human_approval(
        thread_id=thread_id,
        action=payload.action.upper(),
        comments=payload.comments,
        approver_user_id=str(current_user_id),
    )

    await broadcaster.broadcast(
        channel=thread_id,
        event_type="evaluation.completed",
        payload={
            "thread_id": thread_id,
            "status": resumed_state.get("status"),
            "approval_action": resumed_state.get("approval_action"),
            "signature_hash": resumed_state.get("signature_hash"),
        },
    )

    return {
        "thread_id": thread_id,
        "status": resumed_state.get("status"),
        "approval_action": resumed_state.get("approval_action"),
        "approval_comments": resumed_state.get("approval_comments"),
        "signature_hash": resumed_state.get("signature_hash"),
        "decided_at": resumed_state.get("decided_at"),
    }
