"""Node 4: Parallel Compliance and Risk Evaluation Node."""

import uuid
from decimal import Decimal
from typing import Any, Dict, List
from app.agents.compliance_agent import ComplianceAgent
from app.agents.risk_agent import RiskAssessmentAgent
from app.graphs.state import ProcurementEvaluationState
from app.models.compliance import ComplianceRuleType
from app.schemas.compliance import ComplianceInput, ComplianceRuleInput
from app.schemas.risk import RiskInput


def parallel_eval_node(state: ProcurementEvaluationState) -> Dict[str, Any]:
    """Execute Agent 4 (Compliance) and Agent 5 (Risk) for all shortlisted vendors."""
    shortlisted = state.get("shortlisted_vendors", [])
    quotations = {str(q["vendor_id"]): q for q in state.get("quotations", [])}
    raw_rules = state.get("compliance_rules", [])

    # Convert rule dicts to ComplianceRuleInput objects
    rules_inputs: List[ComplianceRuleInput] = []
    if raw_rules:
        for r in raw_rules:
            rules_inputs.append(
                ComplianceRuleInput(
                    rule_id=uuid.UUID(str(r.get("rule_id", uuid.uuid4()))),
                    rule_code=r.get("rule_code", "RULE-GEN"),
                    rule_name=r.get("rule_name", "Policy Rule"),
                    rule_type=ComplianceRuleType(r.get("rule_type", "CERTIFICATION_REQUIRED")),
                    is_mandatory=r.get("is_mandatory", True),
                    parameters=r.get("parameters", {}),
                )
            )
    else:
        # Default compliance rule from spec
        spec = state.get("procurement_spec", {})
        for cert in spec.get("required_certifications", []):
            rules_inputs.append(
                ComplianceRuleInput(
                    rule_code=f"CERT-{cert.upper()}",
                    rule_name=f"Mandatory {cert} Certification",
                    rule_type=ComplianceRuleType.CERTIFICATION_REQUIRED,
                    is_mandatory=True,
                    parameters={"certification_name": cert},
                )
            )

    compliance_results: List[Dict[str, Any]] = []
    risk_results: List[Dict[str, Any]] = []

    for v in shortlisted:
        v_id_str = v.get("vendor_id")
        try:
            v_id = uuid.UUID(str(v_id_str))
        except (ValueError, AttributeError):
            v_id = uuid.uuid5(uuid.NAMESPACE_DNS, str(v_id_str) if v_id_str else "default-vendor")
        v_name = v.get("vendor_name", "Supplier")
        quote = quotations.get(str(v_id_str), {})

        # 1. Evaluate Compliance (Agent 4)
        c_input = ComplianceInput(
            vendor_id=v_id,
            vendor_name=v_name,
            rules=rules_inputs,
            held_certifications=v.get("held_certifications") or v.get("certifications", []),
            quotation_terms={
                "warranty_months": quote.get("warranty_months", 12),
                "payment_terms": quote.get("payment_terms", "Net 30"),
                "incoterms": quote.get("incoterms", "DDP"),
            },
            evidence_text_chunks=v.get("evidence_text_chunks", []),
        )
        c_res = ComplianceAgent.evaluate(c_input)
        compliance_results.append(c_res.model_dump(mode="json"))

        # 2. Evaluate Risk (Agent 5)
        r_input = RiskInput(
            vendor_id=v_id,
            vendor_name=v_name,
            defect_rate=Decimal(str(v.get("defect_rate", "0.0100"))),
            on_time_delivery_rate=Decimal(str(v.get("on_time_delivery_rate", "0.9500"))),
            historical_orders_count=int(v.get("historical_orders_count", 5)),
            spend_concentration_pct=Decimal(str(v.get("spend_concentration_pct", "10.00"))),
            country=v.get("country", "USA"),
            sanction_flag=bool(v.get("sanction_flag", False)),
            qualitative_notes=v.get("qualitative_notes"),
        )
        r_res = RiskAssessmentAgent.assess(r_input)
        risk_results.append(r_res.model_dump(mode="json"))

    return {
        "status": "SCORING",
        "compliance_results": compliance_results,
        "risk_results": risk_results,
    }
