"""Unit tests for Agent 8: Decision Explanation Agent."""

import uuid
from decimal import Decimal
from app.agents.explanation_agent import DecisionExplanationAgent
from app.schemas.explanation import DecisionExplanationInput
from app.schemas.scoring import (
    EvaluationScorecard,
    ScoringPolicyConfig,
    VendorScoreDetail,
)


def test_decision_explanation_normal_case():
    """Verify that a valid scorecard produces a thorough narrative justification."""
    v1_id = uuid.uuid4()
    v2_id = uuid.uuid4()

    winner_score = VendorScoreDetail(
        vendor_id=v1_id,
        vendor_name="AeroPrecision Global",
        is_eligible=True,
        landed_cost_calculated=Decimal("380000.00"),
        landed_cost_score=Decimal("95.00"),
        quality_score=Decimal("90.00"),
        delivery_score=Decimal("88.00"),
        compliance_score=Decimal("100.00"),
        risk_score=Decimal("85.00"),
        terms_score=Decimal("90.00"),
        overall_score=Decimal("91.50"),
        rank=1,
    )

    runner_up_score = VendorScoreDetail(
        vendor_id=v2_id,
        vendor_name="Titan Industrial Ltd",
        is_eligible=True,
        landed_cost_calculated=Decimal("410000.00"),
        landed_cost_score=Decimal("82.00"),
        quality_score=Decimal("85.00"),
        delivery_score=Decimal("80.00"),
        compliance_score=Decimal("95.00"),
        risk_score=Decimal("78.00"),
        terms_score=Decimal("85.00"),
        overall_score=Decimal("83.40"),
        rank=2,
    )

    scorecard = EvaluationScorecard(
        evaluation_id=uuid.uuid4(),
        request_id=uuid.uuid4(),
        policy_id=uuid.uuid4(),
        recommended_vendor_id=v1_id,
        recommended_vendor_name="AeroPrecision Global",
        scores=[winner_score, runner_up_score],
        input_hash="fake-sha256-hash",
    )

    explanation_input = DecisionExplanationInput(
        evaluation_id=scorecard.evaluation_id,
        scorecard=scorecard,
        compliance_results=[],
        risk_results=[],
        policy_config=ScoringPolicyConfig(),
    )

    result = DecisionExplanationAgent.explain(explanation_input)

    assert result.recommended_vendor_id == v1_id
    assert result.recommended_vendor_name == "AeroPrecision Global"
    assert "AeroPrecision Global" in result.executive_summary
    assert "Titan Industrial Ltd" in result.runner_up_comparison
    assert len(result.key_tradeoffs) > 0
    assert len(result.recommended_actions) > 0
    assert result.verification_passed is True


def test_decision_explanation_all_disqualified():
    """Verify that if all vendors are disqualified, explanation indicates no eligible winner."""
    eval_id = uuid.uuid4()
    scorecard = EvaluationScorecard(
        evaluation_id=eval_id,
        request_id=uuid.uuid4(),
        policy_id=uuid.uuid4(),
        recommended_vendor_id=None,
        recommended_vendor_name=None,
        scores=[
            VendorScoreDetail(
                vendor_id=uuid.uuid4(),
                vendor_name="Overbudget Supplier",
                is_eligible=False,
                ineligibility_reasons=["Cost $600,000 exceeds budget ceiling $400,000."],
                landed_cost_calculated=Decimal("600000.00"),
                landed_cost_score=Decimal("0.00"),
                quality_score=Decimal("80.00"),
                delivery_score=Decimal("80.00"),
                compliance_score=Decimal("80.00"),
                risk_score=Decimal("80.00"),
                terms_score=Decimal("80.00"),
                overall_score=Decimal("0.00"),
                rank=1,
            )
        ],
        input_hash="disqualified-hash",
    )

    explanation_input = DecisionExplanationInput(
        evaluation_id=eval_id,
        scorecard=scorecard,
        policy_config=ScoringPolicyConfig(),
    )

    result = DecisionExplanationAgent.explain(explanation_input)

    assert result.recommended_vendor_id is None
    assert "No shortlisted vendor satisfied all mandatory eligibility criteria" in result.executive_summary
