"""Unit tests for Agent 5: Risk Assessment Agent."""

import uuid
from decimal import Decimal
from app.agents.risk_agent import RiskAssessmentAgent
from app.models.risk import RiskTier
from app.schemas.risk import RiskInput


def test_risk_agent_low_risk_vendor():
    """Verify that a proven vendor with strong delivery and quality records receives a LOW risk tier."""
    risk_input = RiskInput(
        vendor_id=uuid.uuid4(),
        vendor_name="Prime Aerospace Components",
        defect_rate=Decimal("0.0050"),  # 0.5% defect rate
        on_time_delivery_rate=Decimal("0.9800"),  # 98% OTD
        historical_orders_count=15,
        spend_concentration_pct=Decimal("15.00"),
        country="USA",
        sanction_flag=False,
    )

    result = RiskAssessmentAgent.assess(risk_input)

    assert result.risk_tier == RiskTier.LOW
    assert result.composite_risk_score < Decimal("25.00")
    assert result.uncertainty_score == Decimal("0.0000")
    assert result.delivery_risk == Decimal("2.00")
    assert result.quality_risk == Decimal("5.00")


def test_risk_agent_sparse_data_penalty():
    """Verify that vendors with no historical orders incur an uncertainty penalty."""
    risk_input = RiskInput(
        vendor_id=uuid.uuid4(),
        vendor_name="New Startup Fab",
        defect_rate=Decimal("0.0000"),
        on_time_delivery_rate=Decimal("1.0000"),
        historical_orders_count=0,
        spend_concentration_pct=Decimal("0.00"),
        country="USA",
    )

    result = RiskAssessmentAgent.assess(risk_input)

    assert result.uncertainty_score == Decimal("0.5000")
    assert any("Sparse historical order" in f.description for f in result.factors)


def test_risk_agent_sanction_triggers_critical_tier():
    """Verify that a sanction flag unconditionally drives the risk tier to CRITICAL."""
    risk_input = RiskInput(
        vendor_id=uuid.uuid4(),
        vendor_name="Sanctioned Global Corp",
        defect_rate=Decimal("0.0100"),
        on_time_delivery_rate=Decimal("0.9500"),
        historical_orders_count=10,
        spend_concentration_pct=Decimal("10.00"),
        country="Russia",
        sanction_flag=True,
    )

    result = RiskAssessmentAgent.assess(risk_input)

    assert result.risk_tier == RiskTier.CRITICAL
    assert result.geopolitical_risk == Decimal("100.00")
    assert any(f.category == "GEOPOLITICAL" for f in result.factors)
