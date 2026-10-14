"""Unit tests for Agent 1: Requirement Analysis Agent."""

from datetime import date
from decimal import Decimal
from app.agents.requirement_agent import RequirementAnalysisAgent
from app.schemas.spec import RawProcurementInput


def test_complete_requirement_analysis():
    """Verify that a fully specified requirement is marked complete without clarification requests."""
    raw = RawProcurementInput(
        text="Need 150 units of Grade 5 Titanium Turbine Casings. Total approved budget is $450,000 USD. Required delivery by 2026-10-31.",
        budget_ceiling=Decimal("450000.00"),
        target_delivery_date=date(2026, 10, 31),
        required_certifications=["ISO-9001", "AS9100"],
    )

    result = RequirementAnalysisAgent.analyze(raw)

    assert result.is_complete is True
    assert len(result.missing_fields) == 0
    assert len(result.clarification_questions) == 0
    assert len(result.spec.items) >= 1
    assert result.spec.items[0].quantity == Decimal("150")
    assert result.spec.budget_ceiling == Decimal("450000.00")
    assert result.spec.target_delivery_date == date(2026, 10, 31)


def test_incomplete_requirement_triggers_clarification():
    """Verify that ambiguous or missing constraints trigger the clarification loop."""
    raw = RawProcurementInput(
        text="We need some replacement titanium alloy casings as soon as possible.",
        # Omit budget ceiling, delivery date, exact quantity
    )

    result = RequirementAnalysisAgent.analyze(raw)

    assert result.is_complete is False
    assert len(result.missing_fields) > 0
    assert "budget_ceiling" in result.missing_fields
    assert "target_delivery_date" in result.missing_fields
    assert len(result.clarification_questions) > 0
