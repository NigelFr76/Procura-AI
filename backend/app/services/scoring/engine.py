"""Authoritative multi-criteria vendor scoring engine and tie-breaking coordinator."""

import hashlib
import json
import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple

from app.schemas.scoring import (
    VendorQuotationInput,
    VendorPerformanceInput,
    VendorComplianceInput,
    VendorRiskInput,
    ProcurementRequirementsInput,
    ScoringPolicyConfig,
    VendorScoreDetail,
    EvaluationScorecard,
)
from app.services.scoring.landed_cost import LandedCostCalculator
from app.services.scoring.normalizer import CriterionNormalizer
from app.services.scoring.eligibility import EligibilityEvaluator


class VendorScoringEngine:
    """Stateless, deterministic domain service for multi-criteria vendor evaluation."""

    SCORING_VERSION = "1.0.0"

    @classmethod
    def evaluate_and_rank(
        cls,
        evaluation_id: uuid.UUID,
        requirements: ProcurementRequirementsInput,
        quotes: List[VendorQuotationInput],
        performances: Dict[uuid.UUID, VendorPerformanceInput],
        compliances: Dict[uuid.UUID, VendorComplianceInput],
        risks: Dict[uuid.UUID, VendorRiskInput],
        policy: ScoringPolicyConfig,
        exchange_rates: Optional[Dict[str, Decimal]] = None,
    ) -> EvaluationScorecard:
        """Execute deterministic evaluation, calculate weighted scores, and establish ranking.
        
        Zero LLM inference. Bit-for-bit reproducible.
        """
        if not quotes:
            raise ValueError("Cannot evaluate empty vendor quotation list.")

        # Step 1: Calculate landed cost for all vendors
        landed_costs: Dict[uuid.UUID, Decimal] = {}
        cost_breakdowns: Dict[uuid.UUID, dict] = {}
        for quote in quotes:
            cost, breakdown = LandedCostCalculator.calculate(
                quote=quote,
                target_currency=requirements.currency,
                exchange_rates=exchange_rates,
            )
            landed_costs[quote.vendor_id] = cost
            cost_breakdowns[quote.vendor_id] = breakdown

        # Step 2: Establish cost bounds across all shortlisted vendors
        all_costs = list(landed_costs.values())
        min_cost = min(all_costs)
        max_cost = max(all_costs)

        # Step 3: Evaluate eligibility and calculate criterion scores per vendor
        scored_vendors: List[VendorScoreDetail] = []
        for quote in quotes:
            v_id = quote.vendor_id
            perf = performances.get(v_id, VendorPerformanceInput(vendor_id=v_id))
            comp = compliances.get(v_id, VendorComplianceInput(vendor_id=v_id))
            risk = risks.get(v_id, VendorRiskInput(vendor_id=v_id))
            landed_cost = landed_costs[v_id]

            # Hard eligibility gate
            is_eligible, ineligibility_reasons = EligibilityEvaluator.evaluate(
                quote=quote,
                compliance=comp,
                requirements=requirements,
                calculated_landed_cost=landed_cost,
            )

            # Normalize individual criteria
            cost_score = CriterionNormalizer.normalize_cost(
                cost=landed_cost,
                min_cost=min_cost,
                max_cost=max_cost,
                budget_ceiling=requirements.budget_ceiling,
            )
            delivery_score = CriterionNormalizer.normalize_delivery(
                quoted_date=quote.quoted_delivery_date,
                target_date=requirements.target_delivery_date,
                max_acceptable_date=requirements.max_acceptable_delivery_date,
            )
            quality_score = CriterionNormalizer.normalize_quality(
                defect_rate=perf.defect_rate,
                on_time_rate=perf.on_time_delivery_rate,
                historical_orders_count=perf.historical_orders_count,
            )
            compliance_score = CriterionNormalizer.normalize_compliance(
                has_unverified_mandatory=comp.has_unverified_mandatory,
                passed_mandatory=comp.passed_mandatory_checks,
                total_mandatory=comp.total_mandatory_checks,
                passed_optional=comp.passed_optional_checks,
                total_optional=comp.total_optional_checks,
            )
            risk_score, confidence_penalty = CriterionNormalizer.normalize_risk(
                composite_risk_score=risk.composite_risk_score,
                uncertainty_score=risk.uncertainty_score,
            )
            terms_score = CriterionNormalizer.normalize_terms(
                payment_terms=quote.payment_terms,
                warranty_months=quote.warranty_months,
            )

            # Weighted composite score
            weighted_total = (
                (cost_score * policy.cost_weight)
                + (quality_score * policy.quality_weight)
                + (delivery_score * policy.delivery_weight)
                + (compliance_score * policy.compliance_weight)
                + (risk_score * policy.risk_weight)
                + (terms_score * policy.terms_weight)
            )

            # Apply uncertainty / missing data penalty
            final_score = max(Decimal("0.0000"), weighted_total - confidence_penalty).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )

            criterion_breakdowns = {
                "landed_cost": {
                    "raw_value": str(landed_cost),
                    "normalized_score": str(cost_score),
                    "weight": str(policy.cost_weight),
                    "weighted_contribution": str((cost_score * policy.cost_weight).quantize(Decimal("0.0001"))),
                    "calculation_details": cost_breakdowns[v_id],
                },
                "quality": {
                    "defect_rate": str(perf.defect_rate),
                    "on_time_rate": str(perf.on_time_delivery_rate),
                    "normalized_score": str(quality_score),
                    "weight": str(policy.quality_weight),
                    "weighted_contribution": str((quality_score * policy.quality_weight).quantize(Decimal("0.0001"))),
                },
                "delivery": {
                    "quoted_delivery_date": str(quote.quoted_delivery_date),
                    "target_delivery_date": str(requirements.target_delivery_date),
                    "normalized_score": str(delivery_score),
                    "weight": str(policy.delivery_weight),
                    "weighted_contribution": str((delivery_score * policy.delivery_weight).quantize(Decimal("0.0001"))),
                },
                "compliance": {
                    "certifications_held": comp.certifications_held,
                    "normalized_score": str(compliance_score),
                    "weight": str(policy.compliance_weight),
                    "weighted_contribution": str((compliance_score * policy.compliance_weight).quantize(Decimal("0.0001"))),
                },
                "risk": {
                    "composite_risk_score": str(risk.composite_risk_score),
                    "normalized_score": str(risk_score),
                    "weight": str(policy.risk_weight),
                    "weighted_contribution": str((risk_score * policy.risk_weight).quantize(Decimal("0.0001"))),
                },
                "terms": {
                    "payment_terms": quote.payment_terms,
                    "warranty_months": quote.warranty_months,
                    "normalized_score": str(terms_score),
                    "weight": str(policy.terms_weight),
                    "weighted_contribution": str((terms_score * policy.terms_weight).quantize(Decimal("0.0001"))),
                },
                "penalties": {
                    "confidence_penalty": str(confidence_penalty),
                    "uncertainty_score": str(risk.uncertainty_score),
                },
            }

            scored_vendors.append(
                VendorScoreDetail(
                    vendor_id=v_id,
                    vendor_name=quote.vendor_name,
                    is_eligible=is_eligible,
                    ineligibility_reasons=ineligibility_reasons,
                    landed_cost_calculated=landed_cost,
                    landed_cost_score=cost_score,
                    quality_score=quality_score,
                    delivery_score=delivery_score,
                    compliance_score=compliance_score,
                    risk_score=risk_score,
                    terms_score=terms_score,
                    confidence_penalty=confidence_penalty,
                    overall_score=final_score,
                    rank=0, # Populated below
                    criterion_breakdowns=criterion_breakdowns,
                )
            )

        # Step 4: Deterministic Sorting & Tie-Breaking
        def sort_key(item: VendorScoreDetail):
            # 1. Eligibility (eligible always ranks ahead of ineligible)
            # 2. Overall Score descending
            # 3. Quality score descending
            # 4. Risk score descending (higher is lower risk)
            # 5. Landed cost ascending (lower cost breaks tie)
            return (
                1 if item.is_eligible else 0,
                item.overall_score,
                item.quality_score,
                item.risk_score,
                -item.landed_cost_calculated,
            )

        scored_vendors.sort(key=sort_key, reverse=True)

        # Assign ranks
        for idx, vendor_score in enumerate(scored_vendors, start=1):
            vendor_score.rank = idx

        # Identify winning recommendation (top ranked eligible vendor)
        recommended_vendor = None
        for v in scored_vendors:
            if v.is_eligible:
                recommended_vendor = v
                break

        # Step 5: Compute cryptographic SHA-256 fingerprint for audit immutability
        input_payload = {
            "requirements": requirements.model_dump(mode="json"),
            "quotes": [q.model_dump(mode="json") for q in quotes],
            "policy": policy.model_dump(mode="json"),
            "scoring_version": cls.SCORING_VERSION,
        }
        input_fingerprint = hashlib.sha256(
            json.dumps(input_payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

        return EvaluationScorecard(
            evaluation_id=evaluation_id,
            request_id=requirements.request_id,
            policy_id=policy.policy_id,
            recommended_vendor_id=recommended_vendor.vendor_id if recommended_vendor else None,
            recommended_vendor_name=recommended_vendor.vendor_name if recommended_vendor else None,
            scores=scored_vendors,
            input_hash=input_fingerprint,
            scoring_version=cls.SCORING_VERSION,
        )
