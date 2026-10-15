"""Conditional routing edges for the procurement LangGraph workflow."""

from langgraph.graph import END
from app.graphs.state import ProcurementEvaluationState


def route_after_intake(state: ProcurementEvaluationState) -> str:
    """Route to discovery if requirements are complete, or halt for clarification."""
    if state.get("is_clarification_needed", False):
        return END
    return "discovery"


def route_after_approval(state: ProcurementEvaluationState) -> str:
    """Route to finalization after human sign-off."""
    return "finalization"
