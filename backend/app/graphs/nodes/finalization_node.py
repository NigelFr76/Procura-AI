"""Node 8: Finalization and Contract Award Node."""

from typing import Any, Dict
from app.graphs.state import ProcurementEvaluationState


def finalization_node(state: ProcurementEvaluationState) -> Dict[str, Any]:
    """Finalize procurement evaluation following human approval gate."""
    action = state.get("approval_action", "APPROVED")

    if action == "APPROVED":
        status = "APPROVED"
    elif action == "REJECTED":
        status = "REJECTED"
    elif action == "MODIFICATION_REQUESTED":
        status = "MODIFICATION_REQUESTED"
    else:
        status = "COMPLETED"

    return {
        "status": status,
    }
