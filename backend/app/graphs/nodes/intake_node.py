"""Node 1: Requirement Intake and Parsing Node."""

from decimal import Decimal
from typing import Any, Dict
from app.agents.requirement_agent import RequirementAnalysisAgent
from app.graphs.state import ProcurementEvaluationState
from app.schemas.spec import RawProcurementInput


def intake_node(state: ProcurementEvaluationState) -> Dict[str, Any]:
    """Execute Agent 1 to parse unstructured requirements and evaluate completeness."""
    raw = state.get("raw_input", {})
    text = raw.get("text", "")
    budget = raw.get("budget_ceiling")
    if budget is not None and not isinstance(budget, Decimal):
        budget = Decimal(str(budget))

    target_date = raw.get("target_delivery_date")
    currency = raw.get("currency", "USD")
    certs = raw.get("required_certifications", [])

    input_data = RawProcurementInput(
        text=text,
        budget_ceiling=budget,
        target_delivery_date=target_date,
        currency=currency,
        required_certifications=certs,
    )

    result = RequirementAnalysisAgent.analyze(input_data)

    if result.is_complete:
        return {
            "status": "DISCOVERY",
            "is_clarification_needed": False,
            "clarification_questions": [],
            "missing_fields": [],
            "spec_result": result.model_dump(mode="json"),
            "procurement_spec": result.spec.model_dump(mode="json"),
        }
    else:
        return {
            "status": "AWAITING_CLARIFICATION",
            "is_clarification_needed": True,
            "clarification_questions": result.clarification_questions,
            "missing_fields": result.missing_fields,
            "spec_result": result.model_dump(mode="json"),
            "procurement_spec": result.spec.model_dump(mode="json"),
        }
