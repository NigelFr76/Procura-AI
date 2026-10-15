"""Node 5: Deterministic Scoring and Ranking Node."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List
from app.graphs.state import ProcurementEvaluationState
from app.schemas.scoring import (
    EvaluationScorecard,
    ProcurementRequirementsInput,
    ScoringPolicyConfig,
    VendorComplianceInput,
    VendorPerformanceInput,
    VendorQuotationInput,
    VendorRiskInput,
)
from app.services.scoring.engine import VendorScoringEngine


def scoring_node(state: ProcurementEvaluationState) -> Dict[str, Any]:
    """Execute authoritative deterministic scoring engine to produce rankings and scorecard."""
    eval_id_str = state.get("evaluation_id") or str(uuid.uuid4())
    eval_id = uuid.UUID(eval_id_str)
    req_id_str = state.get("request_id") or str(uuid.uuid4())
    req_id = uuid.UUID(req_id_str)

    spec = state.get("procurement_spec", {})
    budget = Decimal(str(spec.get("budget_ceiling", "100000.00")))
    
    target_date_val = spec.get("target_delivery_date")
    if isinstance(target_date_val, str):
        target_date = datetime.strptime(target_date_val, "%Y-%m-%d").date()
    elif isinstance(target_date_val, date):
        target_date = target_date_val
    else:
        target_date = date.today()

    requirements = ProcurementRequirementsInput(
        request_id=req_id,
        budget_ceiling=budget,
        target_delivery_date=target_date,
        currency=spec.get("currency", "USD"),
        required_certifications=spec.get("required_certifications", []),
    )

    # Policy
    policy_dict = state.get("scoring_policy")
    if policy_dict:
        policy = ScoringPolicyConfig(**policy_dict)
    else:
        policy = ScoringPolicyConfig()

    # Convert quotations
    quotations_data = state.get("quotations", [])
    quotes: List[VendorQuotationInput] = []
    for q in quotations_data:
        v_id = uuid.UUID(str(q["vendor_id"]))
        q_date_val = q.get("quoted_delivery_date")
        if isinstance(q_date_val, str):
            q_date = datetime.strptime(q_date_val, "%Y-%m-%d").date()
        elif isinstance(q_date_val, date):
            q_date = q_date_val
        else:
            q_date = target_date

        quotes.append(
            VendorQuotationInput(
                vendor_id=v_id,
                vendor_name=q.get("vendor_name", "Supplier"),
                base_price=Decimal(str(q["base_price"])),
                freight_cost=Decimal(str(q.get("freight_cost", "0.00"))),
                insurance_cost=Decimal(str(q.get("insurance_cost", "0.00"))),
                tax_amount=Decimal(str(q.get("tax_amount", "0.00"))),
                discount_amount=Decimal(str(q.get("discount_amount", "0.00"))),
                currency=q.get("currency", "USD"),
                quoted_delivery_date=q_date,
                incoterms=q.get("incoterms", "DDP"),
                payment_terms=q.get("payment_terms", "Net 30"),
                warranty_months=int(q.get("warranty_months", 12)),
            )
        )

    # Convert performance
    shortlisted = state.get("shortlisted_vendors", [])
    performances: Dict[uuid.UUID, VendorPerformanceInput] = {}
    for v in shortlisted:
        v_id = uuid.UUID(str(v["vendor_id"]))
        performances[v_id] = VendorPerformanceInput(
            vendor_id=v_id,
            defect_rate=Decimal(str(v.get("defect_rate", "0.0000"))),
            on_time_delivery_rate=Decimal(str(v.get("on_time_delivery_rate", "1.0000"))),
            historical_orders_count=int(v.get("historical_orders_count", 0)),
        )

    # Convert compliance results
    compliance_results_data = state.get("compliance_results", [])
    vendor_held_certs = {
        uuid.UUID(str(v["vendor_id"])): v.get("held_certifications", [])
        for v in shortlisted
    }
    compliances: Dict[uuid.UUID, VendorComplianceInput] = {}
    for cr in compliance_results_data:
        v_id = uuid.UUID(str(cr["vendor_id"]))
        compliances[v_id] = VendorComplianceInput(
            vendor_id=v_id,
            certifications_held=vendor_held_certs.get(v_id, []),
            passed_mandatory_checks=int(cr.get("passed_mandatory_checks", 0)),
            total_mandatory_checks=int(cr.get("total_mandatory_checks", 0)),
            passed_optional_checks=int(cr.get("passed_optional_checks", 0)),
            total_optional_checks=int(cr.get("total_optional_checks", 0)),
            has_unverified_mandatory=bool(cr.get("has_unverified_mandatory", False)),
        )

    # Convert risk results
    risk_results_data = state.get("risk_results", [])
    risks: Dict[uuid.UUID, VendorRiskInput] = {}
    for rr in risk_results_data:
        v_id = uuid.UUID(str(rr["vendor_id"]))
        risks[v_id] = VendorRiskInput(
            vendor_id=v_id,
            composite_risk_score=Decimal(str(rr.get("composite_risk_score", "0.00"))),
            uncertainty_score=Decimal(str(rr.get("uncertainty_score", "0.0000"))),
        )

    # Execute authoritative scoring engine
    scorecard: EvaluationScorecard = VendorScoringEngine.evaluate_and_rank(
        evaluation_id=eval_id,
        requirements=requirements,
        quotes=quotes,
        performances=performances,
        compliances=compliances,
        risks=risks,
        policy=policy,
    )

    return {
        "status": "EXPLAINING",
        "scoring_policy": policy.model_dump(mode="json"),
        "scorecard": scorecard.model_dump(mode="json"),
    }
