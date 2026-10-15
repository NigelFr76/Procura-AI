"""Interactive CLI demonstration of the complete Multi-Agent LangGraph Procurement Platform."""

import sys
import uuid
from decimal import Decimal

# Ensure backend root is in sys.path
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.coordinator_agent import coordinator


def run_interactive_demo():
    print("\n" + "=" * 70)
    print("  🚀 PROCUREAI: MULTI-AGENT PROCUREMENT & INTELLIGENCE PLATFORM")
    print("  Orchestrated with LangGraph • Deterministic Scoring • HITL Gate")
    print("=" * 70 + "\n")

    thread_id = f"demo-{uuid.uuid4().hex[:8]}"
    org_id = str(uuid.uuid4())

    vendor_1_id = str(uuid.uuid4())
    vendor_2_id = str(uuid.uuid4())

    candidate_vendors = [
        {
            "vendor_id": vendor_1_id,
            "vendor_name": "AeroPrecision Global Ltd",
            "certifications": ["ISO-9001", "AS9100"],
            "historical_orders_count": 14,
            "on_time_delivery_rate": 0.98,
            "defect_rate": 0.004,
            "spend_concentration_pct": 12.0,
        },
        {
            "vendor_id": vendor_2_id,
            "vendor_name": "Titan Heavy Industries",
            "certifications": ["ISO-9001", "AS9100"],
            "historical_orders_count": 9,
            "on_time_delivery_rate": 0.89,
            "defect_rate": 0.015,
            "spend_concentration_pct": 28.0,
        },
    ]

    compliance_rules = [
        {
            "rule_id": str(uuid.uuid4()),
            "rule_code": "CERT-AS9100",
            "rule_name": "AS9100 Aerospace Quality",
            "rule_type": "CERTIFICATION_REQUIRED",
            "is_mandatory": True,
            "parameters": {"certification_name": "AS9100"},
        },
        {
            "rule_id": str(uuid.uuid4()),
            "rule_code": "THRES-WARRANTY",
            "rule_name": "Minimum 12 Months Warranty",
            "rule_type": "DETERMINISTIC_THRESHOLD",
            "is_mandatory": True,
            "parameters": {"min_warranty_months": 12},
        },
    ]

    quotations = [
        {
            "vendor_id": vendor_1_id,
            "vendor_name": "AeroPrecision Global Ltd",
            "base_price": "360000.00",
            "freight_cost": "4500.00",
            "insurance_cost": "1200.00",
            "tax_amount": "18000.00",
            "discount_amount": "2500.00",
            "currency": "USD",
            "quoted_delivery_date": "2026-11-20",
            "incoterms": "DDP",
            "payment_terms": "Net 30",
            "warranty_months": 24,
        },
        {
            "vendor_id": vendor_2_id,
            "vendor_name": "Titan Heavy Industries",
            "base_price": "345000.00",
            "freight_cost": "6000.00",
            "insurance_cost": "1500.00",
            "tax_amount": "17250.00",
            "discount_amount": "1000.00",
            "currency": "USD",
            "quoted_delivery_date": "2026-11-28",
            "incoterms": "DDP",
            "payment_terms": "Net 30",
            "warranty_months": 12,
        },
    ]

    raw_rfp_text = (
        "Procurement RFP: Need 150 units of Grade 5 Titanium Turbine Casings. "
        "Total approved budget ceiling is $450,000 USD. "
        "Required delivery deadline is 2026-11-30. Mandatory AS9100 aerospace certification."
    )

    print("📄 [1/5] Submitting Raw Procurement Request to Agent 1 (Intake Agent)...")
    print(f"    RFP: \"{raw_rfp_text}\"\n")

    interrupted_state = coordinator.start_evaluation(
        raw_text=raw_rfp_text,
        organization_id=org_id,
        budget_ceiling=450000.00,
        target_delivery_date="2026-11-30",
        currency="USD",
        required_certifications=["AS9100"],
        candidate_vendors=candidate_vendors,
        compliance_rules=compliance_rules,
        quotations=quotations,
        thread_id=thread_id,
    )

    print("🔍 [2/5] Multi-Agent Pipeline Executed:")
    print("    • Agent 1 (Requirement Analysis): Specifications and constraints validated.")
    print("    • Agent 2 (Vendor Discovery): 2 suppliers qualified against technical registry.")
    print("    • Agent 3 (Quotation Analysis): Extracted commercial pricing & DDP terms.")
    print("    • Agent 4 (Compliance Agent): 100% mandatory compliance rules verified.")
    print("    • Agent 5 (Risk Assessment): Operational risk, OTD, and defect rates analyzed.")
    print("    • Phase 3 Deterministic Scoring Engine: Landed cost & weighted criteria ranked.")
    print("    • Agent 8 (Decision Explanation): Anti-hallucination audit narrative synthesized.\n")

    scorecard = interrupted_state.get("scorecard", {})
    explanation = interrupted_state.get("decision_explanation", {})

    print("📊 [3/5] Authoritative Deterministic Scorecard:")
    for s in scorecard.get("scores", []):
        score_val = float(s['overall_score'])
        cost_val = float(s['landed_cost_calculated'])
        qual_val = float(s['quality_score'])
        del_val = float(s['delivery_score'])
        print(
            f"    Rank #{s['rank']}: {s['vendor_name']} | Overall Score: {score_val:.2f}/100 "
            f"| Landed Cost: ${cost_val:,.2f} | Quality: {qual_val:.1f} | Delivery: {del_val:.1f}"
        )

    print(f"\n    🏆 Recommended Winner: {scorecard.get('recommended_vendor_name')}")
    print(f"    🔒 Input Cryptographic Hash: {scorecard.get('input_hash')[:16]}...")

    print("\n🧠 [4/5] Audit Narrative (Agent 8):")
    print(f"    Executive Summary: {explanation.get('executive_summary')}")
    print(f"    Runner-up Delta:   {explanation.get('runner_up_comparison')}")

    print("\n" + "-" * 70)
    print("  ⏸️  LANGGRAPH HUMAN-IN-THE-LOOP APPROVAL GATE (INTERRUPT)")
    print("  Execution has halted. Awaiting human procurement officer authorization.")
    print("-" * 70)

    # Prompt user or auto-approve
    print("\nSimulating Human Approver Sign-off:")
    print("    Approver: Chief Procurement Officer (cpo-executive@enterprise.com)")
    print("    Decision: APPROVED")
    print("    Comments: 'Evaluated landed cost and quality delta. Authorized for award.'\n")

    final_state = coordinator.submit_human_approval(
        thread_id=thread_id,
        action="APPROVED",
        comments="Evaluated landed cost and quality delta. Authorized for award.",
        approver_user_id="cpo-executive-001",
    )

    print("✅ [5/5] Final Decision Recorded:")
    print(f"    Workflow Status:    {final_state.get('status')}")
    print(f"    Award Decision:     {final_state.get('approval_action')}")
    print(f"    Decided At:         {final_state.get('decided_at')}")
    print(f"    Signature Hash:     {final_state.get('signature_hash')}")
    print("\n" + "=" * 70)
    print("  🎉 End-to-end multi-agent evaluation completed successfully!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_interactive_demo()
