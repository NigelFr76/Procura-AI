"""Unit tests for Agent 6: Negotiation Simulation Agent."""

import uuid
from decimal import Decimal
from app.agents.negotiation_agent import NegotiationSimulationAgent
from app.schemas.negotiation import NegotiationSimInput


def test_negotiation_simulation_normal_flow():
    """Verify that multi-round negotiation produces counteroffers strictly respecting the cost floor."""
    v_id = uuid.uuid4()
    sim_input = NegotiationSimInput(
        vendor_id=v_id,
        vendor_name="Titan Aerospace Ltd",
        quoted_base_price=Decimal("500000.00"),
        quoted_delivery_days=45,
        quoted_payment_terms="Net 30",
        quoted_warranty_months=12,
        target_price_discount_pct=Decimal("12.00"),
        target_payment_terms="Net 60",
        vendor_elasticity_score=0.6,
        cost_floor_pct=Decimal("85.00"),  # Floor = $425,000.00
    )

    result = NegotiationSimulationAgent.simulate(sim_input)

    assert result.vendor_id == v_id
    assert result.is_hypothetical_simulation is True
    assert len(result.rounds) == 3
    assert result.walkaway_price == Decimal("425000.00")
    
    # Invariants
    assert result.expected_final_price >= Decimal("425000.00")
    assert result.expected_final_price < Decimal("500000.00")
    assert result.projected_savings_amount > Decimal("0.00")
    assert result.projected_savings_pct > Decimal("0.00")
    assert len(result.tactical_recommendations) >= 3


def test_negotiation_simulation_cost_floor_enforcement():
    """Verify that an aggressive discount target cannot drive final price below cost floor."""
    sim_input = NegotiationSimInput(
        vendor_id=uuid.uuid4(),
        vendor_name="Strict Margins Inc",
        quoted_base_price=Decimal("100000.00"),
        target_price_discount_pct=Decimal("40.00"),  # Asks for 40% discount ($60,000)
        cost_floor_pct=Decimal("88.00"),            # Floor is $88,000
        vendor_elasticity_score=0.9,
    )

    result = NegotiationSimulationAgent.simulate(sim_input)

    # Must not breach cost floor
    assert result.expected_final_price >= Decimal("88000.00")
    for r in result.rounds:
        assert r.vendor_counter_price >= Decimal("88000.00")
