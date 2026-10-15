"""Integration tests for What-If scenario simulation REST endpoint."""

import uuid
from datetime import date
from decimal import Decimal
import pytest
from httpx import AsyncClient

from app.schemas.scoring import (
    ProcurementRequirementsInput,
    ScoringPolicyConfig,
    VendorComplianceInput,
    VendorPerformanceInput,
    VendorQuotationInput,
    VendorRiskInput,
)
from app.services.scoring.engine import VendorScoringEngine


@pytest.mark.asyncio
async def test_api_scenario_simulation_endpoint(async_client: AsyncClient):
    """Test scenario simulation endpoint with parameter override and winner displacement."""
    v1_id = uuid.uuid4()
    v2_id = uuid.uuid4()
    eval_id = uuid.uuid4()

    requirements = ProcurementRequirementsInput(
        request_id=uuid.uuid4(),
        budget_ceiling=Decimal("300000.00"),
        target_delivery_date=date(2026, 12, 1),
    )

    q1 = VendorQuotationInput(
        vendor_id=v1_id,
        vendor_name="Baseline Winner Co",
        base_price=Decimal("180000.00"),
        quoted_delivery_date=date(2026, 11, 20),
    )
    q2 = VendorQuotationInput(
        vendor_id=v2_id,
        vendor_name="Runner-Up Corp",
        base_price=Decimal("240000.00"),
        quoted_delivery_date=date(2026, 11, 25),
    )

    performances = {
        v1_id: VendorPerformanceInput(vendor_id=v1_id),
        v2_id: VendorPerformanceInput(vendor_id=v2_id),
    }
    compliances = {
        v1_id: VendorComplianceInput(vendor_id=v1_id),
        v2_id: VendorComplianceInput(vendor_id=v2_id),
    }
    risks = {
        v1_id: VendorRiskInput(vendor_id=v1_id),
        v2_id: VendorRiskInput(vendor_id=v2_id),
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

    # Build REST payload for /api/v1/scenarios/simulate
    scenario_payload = {
        "scenario_name": "Runner-Up Aggressive Discount",
        "scenario_description": "Simulate Runner-Up cutting price to $160,000",
        "baseline_evaluation_id": str(eval_id),
        "baseline_requirements": requirements.model_dump(mode="json"),
        "baseline_quotes": [q.model_dump(mode="json") for q in [q1, q2]],
        "baseline_performances": {str(k): v.model_dump(mode="json") for k, v in performances.items()},
        "baseline_compliances": {str(k): v.model_dump(mode="json") for k, v in compliances.items()},
        "baseline_risks": {str(k): v.model_dump(mode="json") for k, v in risks.items()},
        "baseline_policy": policy.model_dump(mode="json"),
        "baseline_scorecard": baseline_scorecard.model_dump(mode="json"),
        "overrides": {
            "vendor_price_overrides": {str(v2_id): "160000.00"},
        },
    }

    resp = await async_client.post("/api/v1/scenarios/simulate", json=scenario_payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["winner_displaced"] is True
    assert data["previous_winner_id"] == str(v1_id)
    assert data["new_winner_id"] == str(v2_id)
    assert "WINNER DISPLACEMENT DETECTED" in data["causal_explanation"]
    assert len(data["vendor_differentials"]) == 2
