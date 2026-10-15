"""Node 7: Human-in-the-Loop Approval Interrupt Gate Node."""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict
from langgraph.types import interrupt

from app.graphs.state import ProcurementEvaluationState


def approval_gate_node(state: ProcurementEvaluationState) -> Dict[str, Any]:
    """Halt state machine execution and yield control to human procurement officer."""
    scorecard = state.get("scorecard", {})
    explanation = state.get("decision_explanation", {})
    eval_id = state.get("evaluation_id", "")

    # Trigger LangGraph interrupt - persists state to checkpointer and halts
    human_input = interrupt({
        "type": "PROCUREMENT_APPROVAL_REQUIRED",
        "evaluation_id": eval_id,
        "recommended_vendor_id": scorecard.get("recommended_vendor_id"),
        "recommended_vendor_name": scorecard.get("recommended_vendor_name"),
        "scorecard": scorecard,
        "explanation": explanation,
        "prompt": "Review evaluation and authorize final vendor award.",
    })

    # Resumed execution with human officer input
    if isinstance(human_input, dict):
        action = human_input.get("action", "APPROVED")
        comments = human_input.get("comments", "Approved without modification.")
        approver_id = human_input.get("approver_user_id", "system-officer")
    else:
        action = str(human_input)
        comments = "Approved."
        approver_id = "system-officer"

    decided_at = datetime.now(timezone.utc).isoformat()
    raw_sig = f"{eval_id}:{action}:{approver_id}:{decided_at}"
    sig_hash = hashlib.sha256(raw_sig.encode()).hexdigest()

    return {
        "approval_status": action,
        "approval_action": action,
        "approval_comments": comments,
        "approver_user_id": approver_id,
        "signature_hash": sig_hash,
        "decided_at": decided_at,
    }
