"""Unit tests for ScenarioSimulationEngine and What-If differential analysis."""

import copy
import uuid
from datetime import date
from decimal import Decimal

from app.schemas.scenario import (
    ScenarioParameterOverrides,
    ScenarioRunInput,
)
from app.schemas.scoring import (
    EvaluationScorecard,
    ProcurementRequirementsInput,
    ScoringPolicyConfig,
    VendorComplianceInput,
    VendorPerformanceInput,
    VendorQuotationInput,
    VendorRiskInput,
    VendorScoreDetail,
)
from app.services.scenarios.scenario_engine import ScenarioSimulationEngine
from app.services.scoring.engine import VendorScoringEngine


def test_scenario_simulation_winner_displacement_via_price_reduction():
    """Verify that a price override on Rank 2 supplier triggers winner displacement and causal explanation."""
    v1_id = uuid.uuid4()
    v2_id = uuid.uuid4()
    req_id = uuid.uuid4()
    eval_id = uuid.uuid4()

    requirements = ProcurementRequirementsInput(
        request_id=req_id,
        budget_ceiling=Decimal("500000.00"),
        target_delivery_date=date(2026, 12, 1),
        required_certifications=["ISO-9001"],
    )

    # Baseline: v1 is cheaper ($300k vs $380k) and wins Rank 1
    q1 = VendorQuotationInput(
        vendor_id=v1_id,
        vendor_name="Alpha Supplies",
        base_price=Decimal("300000.00"),
        quoted_delivery_date=date(2026, 11, 20),
    )
    q2 = VendorQuotationInput(
        vendor_id=v2_id,
        vendor_name="Beta Technologies",
        base_price=Decimal("380000.00"),
        quoted_delivery_date=date(2026, 11, 20),
    )

    performances = {
        v1_id: VendorPerformanceInput(vendor_id=v1_id, defect_rate=Decimal("0.01"), on_time_delivery_rate=Decimal("0.95")),
        v2_id: VendorPerformanceInput(vendor_id=v2_id, defect_rate=Decimal("0.002"), on_time_delivery_rate=Decimal("0.99")),
    }
    compliances = {
        v1_id: VendorComplianceInput(vendor_id=v1_id, certifications_held=["ISO-9001"]),
        v2_id: VendorComplianceInput(vendor_id=v2_id, certifications_held=["ISO-9001"]),
    }
    risks = {
        v1_id: VendorRiskInput(vendor_id=v1_id, composite_risk_score=Decimal("20.00")),
        v2_id: VendorRiskInput(vendor_id=v2_id, composite_risk_score=Decimal("10.00")),
    }
    policy = ScoringPolicyConfig()

    baseline_scorecard = VendorScoringEngine.evaluate_and_rank(
        evaluation_id=eval_id,
        requirements=requirements,
        quotes=[q1, q2],
        performances=performances,
        compliances=compliances,
        risks=risks,
        policy=policy,
    )

    assert baseline_scorecard.recommended_vendor_id == v1_id

    # Deep copy baseline before scenario to test immutability
    original_base_price_q2 = Decimal(str(q2.base_price))

    # Scenario: Beta drops price from $380,000 to $270,000 (cheaper than Alpha)
    scenario_input = ScenarioRunInput(
        scenario_name="Beta Concession Strategy",
        scenario_description="Simulate Beta offering 29% price concession",
        baseline_evaluation_id=eval_id,
        baseline_requirements=requirements,
        baseline_quotes=[q1, q2],
        baseline_performances=performances,
        baseline_compliances=compliances,
        baseline_risks=risks,
        baseline_policy=policy,
        baseline_scorecard=baseline_scorecard,
        overrides=ScenarioParameterOverrides(
            vendor_price_overrides={v2_id: Decimal("270000.00")},
        ),
    )

    result = ScenarioSimulationEngine.execute_scenario(scenario_input)

    # Invariant 1: Baseline was NOT mutated
    assert q2.base_price == original_base_price_q2
    assert result.baseline_immutable_verified is True

    # Invariant 2: Winner was displaced to Beta Technologies
    assert result.winner_displaced is True
    assert result.previous_winner_id == v1_id
    assert result.new_winner_id == v2_id
    assert "WINNER DISPLACEMENT DETECTED" in result.causal_explanation
    assert "Beta Technologies" in result.causal_explanation

    # Invariant 3: Differentials correctly quantified
    beta_diff = next(d for d in result.vendor_differentials if d.vendor_id == v2_id)
    assert beta_diff.rank_delta == 1  # Moved from 2 to 1 (+1)
    assert beta_diff.baseline_rank == 2
    assert beta_diff.scenario_rank == 1
    assert beta_diff.cost_delta < Decimal("0.00")
    assert beta_diff.score_delta > Decimal("0.00")


def test_scenario_simulation_cert_revocation_disqualification():
    """Verify that simulating a certification revocation marks the baseline winner ineligible."""
    v1_id = uuid.uuid4()
    req_id = uuid.uuid4()
    eval_id = uuid.uuid4()

    requirements = ProcurementRequirementsInput(
        request_id=req_id,
        budget_ceiling=Decimal("500000.00"),
        target_delivery_date=date(2026, 12, 1),
        required_certifications=["AS9100"],
    )

    q1 = VendorQuotationInput(
        vendor_id=v1_id,
        vendor_name="Solo Aerospace",
        base_price=Decimal("400000.00"),
        quoted_delivery_date=date(2026, 11, 20),
    )

    performances = {v1_id: VendorPerformanceInput(vendor_id=v1_id)}
    compliances = {v1_id: VendorComplianceInput(vendor_id=v1_id, certifications_held=["AS9100"])}
    risks = {v1_id: VendorRiskInput(vendor_id=v1_id)}
    policy = ScoringPolicyConfig()

    baseline_scorecard = VendorScoringEngine.evaluate_and_rank(
        evaluation_id=eval_id,
        requirements=requirements,
        quotes=[q1],
        performances=performances,
        compliances=compliances,
        risks=risks,
        policy=policy,
    )
    assert baseline_scorecard.scores[0].is_eligible is True

    # Scenario: Revoke AS9100
    scenario_input = ScenarioRunInput(
        scenario_name="Quality Audit Revocation",
        baseline_evaluation_id=eval_id,
        baseline_requirements=requirements,
        baseline_quotes=[q1],
        baseline_performances=performances,
        baseline_compliances=compliances,
        baseline_risks=risks,
        baseline_policy=policy,
        baseline_scorecard=baseline_scorecard,
        overrides=ScenarioParameterOverrides(
            vendor_cert_revocations={v1_id: ["AS9100"]},
        ),
    )

    result = ScenarioSimulationEngine.execute_scenario(scenario_input)

    diff = result.vendor_differentials[0]
    assert diff.baseline_eligible is True
    assert diff.scenario_eligible is False
    assert diff.eligibility_shifted is True
    assert result.scenario_scorecard.recommended_vendor_id is None
