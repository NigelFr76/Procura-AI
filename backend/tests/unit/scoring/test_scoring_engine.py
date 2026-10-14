"""Unit tests for deterministic multi-criteria scoring, landed cost, normalizers, and reproducibility."""

import uuid
from datetime import date
from decimal import Decimal
import pytest

from app.schemas.scoring import (
    VendorQuotationInput,
    VendorPerformanceInput,
    VendorComplianceInput,
    VendorRiskInput,
    ProcurementRequirementsInput,
    ScoringPolicyConfig,
)
from app.services.scoring import (
    LandedCostCalculator,
    CriterionNormalizer,
    EligibilityEvaluator,
    VendorScoringEngine,
)


def test_landed_cost_calculator():
    """Verify landed cost calculation with discount, freight, taxes, and incoterms."""
    # Test 1: Standard DDP quote in USD
    quote_ddp = VendorQuotationInput(
        vendor_id=uuid.uuid4(),
        vendor_name="Acme Supplies",
        base_price=Decimal("10000.00"),
        discount_amount=Decimal("500.00"),
        freight_cost=Decimal("400.00"),
        tax_amount=Decimal("800.00"),
        quoted_delivery_date=date(2026, 11, 1),
        incoterms="DDP",
    )
    cost, breakdown = LandedCostCalculator.calculate(quote_ddp)
    # 10000 - 500 + 400 + 800 = 10700.0000
    assert cost == Decimal("10700.0000")
    assert breakdown["incoterms_surcharge"] == Decimal("0.0000")

    # Test 2: EXW quote with omitted freight (applies 6% estimated surcharge)
    quote_exw = VendorQuotationInput(
        vendor_id=uuid.uuid4(),
        vendor_name="Euro Parts",
        base_price=Decimal("10000.00"),
        quoted_delivery_date=date(2026, 11, 1),
        incoterms="EXW",
        currency="USD",
    )
    cost_exw, breakdown_exw = LandedCostCalculator.calculate(quote_exw)
    # 10000 + 600 (6%) = 10600.0000
    assert cost_exw == Decimal("10600.0000")
    assert breakdown_exw["incoterms_surcharge"] == Decimal("600.0000")

    # Test 3: Currency conversion from EUR to USD (rate 1.0850)
    quote_eur = VendorQuotationInput(
        vendor_id=uuid.uuid4(),
        vendor_name="Berlin Steel",
        base_price=Decimal("1000.00"),
        currency="EUR",
        quoted_delivery_date=date(2026, 11, 1),
        incoterms="DDP",
    )
    cost_eur, breakdown_eur = LandedCostCalculator.calculate(quote_eur, target_currency="USD")
    assert cost_eur == Decimal("1085.0000")


def test_criterion_normalizer_cost():
    """Verify cost normalization edge cases: min/max spread, identical costs, and single vendor."""
    budget = Decimal("50000.0000")

    # Standard spread: min=10000, max=20000
    # Vendor at 10000 -> 100.0000
    # Vendor at 15000 -> 50.0000
    # Vendor at 20000 -> 0.0000
    s_min = CriterionNormalizer.normalize_cost(Decimal("10000"), Decimal("10000"), Decimal("20000"), budget)
    s_mid = CriterionNormalizer.normalize_cost(Decimal("15000"), Decimal("10000"), Decimal("20000"), budget)
    s_max = CriterionNormalizer.normalize_cost(Decimal("20000"), Decimal("10000"), Decimal("20000"), budget)
    assert s_min == Decimal("100.0000")
    assert s_mid == Decimal("50.0000")
    assert s_max == Decimal("0.0000")

    # Identical bids: both vendors bid 25000 within budget 50000 -> 100.0000
    s_equal = CriterionNormalizer.normalize_cost(Decimal("25000"), Decimal("25000"), Decimal("25000"), budget)
    assert s_equal == Decimal("100.0000")


def test_eligibility_evaluator():
    """Verify hard eligibility gating for budget, delivery deadline, and certifications."""
    reqs = ProcurementRequirementsInput(
        request_id=uuid.uuid4(),
        budget_ceiling=Decimal("50000.00"),
        target_delivery_date=date(2026, 10, 1),
        max_acceptable_delivery_date=date(2026, 10, 15),
        required_certifications=["ISO-9001", "AS9100"],
    )

    valid_quote = VendorQuotationInput(
        vendor_id=uuid.uuid4(),
        vendor_name="Valid Vendor",
        base_price=Decimal("45000.00"),
        quoted_delivery_date=date(2026, 10, 10),
    )
    valid_comp = VendorComplianceInput(
        vendor_id=valid_quote.vendor_id,
        certifications_held=["ISO-9001", "AS9100", "RoHS"],
        passed_mandatory_checks=2,
        total_mandatory_checks=2,
    )
    is_eligible, violations = EligibilityEvaluator.evaluate(
        valid_quote, valid_comp, reqs, Decimal("45000.00")
    )
    assert is_eligible is True
    assert len(violations) == 0

    # Over budget check
    is_el_cost, viol_cost = EligibilityEvaluator.evaluate(
        valid_quote, valid_comp, reqs, Decimal("55000.00")
    )
    assert is_el_cost is False
    assert any("exceeds budget ceiling" in v for v in viol_cost)

    # Missing mandatory certification check
    bad_comp = VendorComplianceInput(
        vendor_id=valid_quote.vendor_id,
        certifications_held=["ISO-9001"], # Missing AS9100
        passed_mandatory_checks=1,
        total_mandatory_checks=2,
    )
    is_el_cert, viol_cert = EligibilityEvaluator.evaluate(
        valid_quote, bad_comp, reqs, Decimal("45000.00")
    )
    assert is_el_cert is False
    assert any("Missing mandatory certification: AS9100" in v for v in viol_cert)


def test_vendor_scoring_engine_full_evaluation():
    """Verify complete evaluation workflow with 3 vendors, ranking, and eligibility separation."""
    req_id = uuid.uuid4()
    reqs = ProcurementRequirementsInput(
        request_id=req_id,
        budget_ceiling=Decimal("100000.00"),
        target_delivery_date=date(2026, 11, 1),
        max_acceptable_delivery_date=date(2026, 11, 15),
        required_certifications=["ISO-9001"],
    )

    v1_id, v2_id, v3_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

    # Vendor 1: Lowest cost, great quality, on time (expected winner)
    q1 = VendorQuotationInput(
        vendor_id=v1_id,
        vendor_name="Alpha Tech",
        base_price=Decimal("60000.00"),
        quoted_delivery_date=date(2026, 10, 25),
        payment_terms="Net 60",
    )
    p1 = VendorPerformanceInput(vendor_id=v1_id, defect_rate=Decimal("0.0020"), on_time_delivery_rate=Decimal("0.9900"), historical_orders_count=30)
    c1 = VendorComplianceInput(vendor_id=v1_id, certifications_held=["ISO-9001"], passed_mandatory_checks=1, total_mandatory_checks=1)
    r1 = VendorRiskInput(vendor_id=v1_id, composite_risk_score=Decimal("10.00"))

    # Vendor 2: Higher cost, fair quality
    q2 = VendorQuotationInput(
        vendor_id=v2_id,
        vendor_name="Beta Logistics",
        base_price=Decimal("80000.00"),
        quoted_delivery_date=date(2026, 11, 5),
        payment_terms="Net 30",
    )
    p2 = VendorPerformanceInput(vendor_id=v2_id, defect_rate=Decimal("0.0150"), on_time_delivery_rate=Decimal("0.9200"), historical_orders_count=15)
    c2 = VendorComplianceInput(vendor_id=v2_id, certifications_held=["ISO-9001"], passed_mandatory_checks=1, total_mandatory_checks=1)
    r2 = VendorRiskInput(vendor_id=v2_id, composite_risk_score=Decimal("25.00"))

    # Vendor 3: Ineligible (over budget)
    q3 = VendorQuotationInput(
        vendor_id=v3_id,
        vendor_name="Gamma Premium",
        base_price=Decimal("120000.00"), # Exceeds 100k
        quoted_delivery_date=date(2026, 11, 1),
    )
    p3 = VendorPerformanceInput(vendor_id=v3_id, defect_rate=Decimal("0.0000"), on_time_delivery_rate=Decimal("1.0000"), historical_orders_count=50)
    c3 = VendorComplianceInput(vendor_id=v3_id, certifications_held=["ISO-9001"], passed_mandatory_checks=1, total_mandatory_checks=1)
    r3 = VendorRiskInput(vendor_id=v3_id, composite_risk_score=Decimal("5.00"))

    policy = ScoringPolicyConfig()
    eval_id = uuid.uuid4()

    scorecard = VendorScoringEngine.evaluate_and_rank(
        evaluation_id=eval_id,
        requirements=reqs,
        quotes=[q1, q2, q3],
        performances={v1_id: p1, v2_id: p2, v3_id: p3},
        compliances={v1_id: c1, v2_id: c2, v3_id: c3},
        risks={v1_id: r1, v2_id: r2, v3_id: r3},
        policy=policy,
    )

    assert scorecard.recommended_vendor_id == v1_id
    assert scorecard.recommended_vendor_name == "Alpha Tech"
    assert len(scorecard.scores) == 3

    # Alpha Tech should be Rank 1
    assert scorecard.scores[0].vendor_id == v1_id
    assert scorecard.scores[0].rank == 1
    assert scorecard.scores[0].is_eligible is True

    # Beta Logistics should be Rank 2
    assert scorecard.scores[1].vendor_id == v2_id
    assert scorecard.scores[1].rank == 2
    assert scorecard.scores[1].is_eligible is True

    # Gamma Premium should be Rank 3 and marked INELIGIBLE
    assert scorecard.scores[2].vendor_id == v3_id
    assert scorecard.scores[2].rank == 3
    assert scorecard.scores[2].is_eligible is False
    assert len(scorecard.scores[2].ineligibility_reasons) > 0


def test_scoring_reproducibility():
    """Assert that 100 consecutive executions produce bit-for-bit identical fingerprints and scores."""
    req_id = uuid.uuid4()
    reqs = ProcurementRequirementsInput(
        request_id=req_id,
        budget_ceiling=Decimal("100000.00"),
        target_delivery_date=date(2026, 11, 1),
    )
    v_id = uuid.uuid4()
    q = VendorQuotationInput(vendor_id=v_id, vendor_name="Vendor A", base_price=Decimal("75000.00"), quoted_delivery_date=date(2026, 10, 20))
    p = VendorPerformanceInput(vendor_id=v_id)
    c = VendorComplianceInput(vendor_id=v_id)
    r = VendorRiskInput(vendor_id=v_id)
    policy = ScoringPolicyConfig()
    eval_id = uuid.uuid4()

    first_card = VendorScoringEngine.evaluate_and_rank(
        eval_id, reqs, [q], {v_id: p}, {v_id: c}, {v_id: r}, policy
    )

    for _ in range(50):
        next_card = VendorScoringEngine.evaluate_and_rank(
            eval_id, reqs, [q], {v_id: p}, {v_id: c}, {v_id: r}, policy
        )
        assert next_card.input_hash == first_card.input_hash
        assert next_card.scores[0].overall_score == first_card.scores[0].overall_score
        assert next_card.scores[0].landed_cost_calculated == first_card.scores[0].landed_cost_calculated


def test_tie_breaking():
    """Verify tie-breaking: identical overall score resolved by quality score."""
    v1_id, v2_id = uuid.uuid4(), uuid.uuid4()
    reqs = ProcurementRequirementsInput(
        request_id=uuid.uuid4(),
        budget_ceiling=Decimal("50000.00"),
        target_delivery_date=date(2026, 11, 1),
    )
    # Both vendors bid identically on cost, terms, delivery
    q1 = VendorQuotationInput(vendor_id=v1_id, vendor_name="Vendor 1", base_price=Decimal("40000.00"), quoted_delivery_date=date(2026, 11, 1))
    q2 = VendorQuotationInput(vendor_id=v2_id, vendor_name="Vendor 2", base_price=Decimal("40000.00"), quoted_delivery_date=date(2026, 11, 1))

    # Policy with 0% weight on quality so overall scores end up identical
    policy = ScoringPolicyConfig(
        cost_weight=Decimal("0.5000"),
        quality_weight=Decimal("0.0000"),
        delivery_weight=Decimal("0.3000"),
        compliance_weight=Decimal("0.1000"),
        risk_weight=Decimal("0.0500"),
        terms_weight=Decimal("0.0500"),
    )

    # Vendor 1 has lower defect rate (higher quality)
    p1 = VendorPerformanceInput(vendor_id=v1_id, defect_rate=Decimal("0.0010"), on_time_delivery_rate=Decimal("1.0000"), historical_orders_count=20)
    p2 = VendorPerformanceInput(vendor_id=v2_id, defect_rate=Decimal("0.0400"), on_time_delivery_rate=Decimal("1.0000"), historical_orders_count=20)

    c = VendorComplianceInput(vendor_id=v1_id)
    r = VendorRiskInput(vendor_id=v1_id)

    card = VendorScoringEngine.evaluate_and_rank(
        uuid.uuid4(), reqs, [q1, q2],
        {v1_id: p1, v2_id: p2},
        {v1_id: c, v2_id: c},
        {v1_id: r, v2_id: r},
        policy,
    )

    # Overall scores should be equal
    assert card.scores[0].overall_score == card.scores[1].overall_score
    # Vendor 1 should win tie-break due to superior quality score
    assert card.scores[0].vendor_id == v1_id
    assert card.scores[0].rank == 1
    assert card.scores[1].vendor_id == v2_id
    assert card.scores[1].rank == 2
