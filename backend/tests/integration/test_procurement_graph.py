"""Integration tests for Phase 7: LangGraph Multi-Agent Orchestrator & HITL Workflow."""

import uuid
from decimal import Decimal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from app.graphs.procurement_graph import (
    build_procurement_graph,
    execute_evaluation,
    resume_evaluation,
)
from app.graphs.state import ProcurementEvaluationState


def test_procurement_graph_happy_path_with_hitl_approval():
    """Verify end-to-end execution from intake to interrupt gate, and resumption on human approval."""
    checkpointer = MemorySaver()
    graph = build_procurement_graph(checkpointer=checkpointer)

    thread_id = f"test-eval-{uuid.uuid4()}"
    org_id = str(uuid.uuid4())
    req_id = str(uuid.uuid4())
    eval_id = str(uuid.uuid4())

    vendor_a_id = str(uuid.uuid4())
    vendor_b_id = str(uuid.uuid4())

    initial_state: ProcurementEvaluationState = {
        "organization_id": org_id,
        "request_id": req_id,
        "evaluation_id": eval_id,
        "thread_id": thread_id,
        "status": "INTAKE",
        "is_clarification_needed": False,
        "clarification_questions": [],
        "missing_fields": [],
        "raw_input": {
            "text": "Need 100 high-precision CNC titanium housings. Budget is $200,000 USD. Required delivery by 2026-11-30.",
            "budget_ceiling": 200000.00,
            "target_delivery_date": "2026-11-30",
            "currency": "USD",
            "required_certifications": ["ISO-9001"],
            "candidate_vendors": [
                {
                    "vendor_id": vendor_a_id,
                    "vendor_name": "AeroPrecision CNC",
                    "certifications": ["ISO-9001"],
                    "historical_orders_count": 12,
                    "on_time_delivery_rate": 0.98,
                    "defect_rate": 0.005,
                    "spend_concentration_pct": 15.0,
                },
                {
                    "vendor_id": vendor_b_id,
                    "vendor_name": "Precision Fabworks",
                    "certifications": ["ISO-9001"],
                    "historical_orders_count": 8,
                    "on_time_delivery_rate": 0.90,
                    "defect_rate": 0.02,
                    "spend_concentration_pct": 25.0,
                },
            ],
        },
        "scoring_policy": {},
        "compliance_rules": [
            {
                "rule_id": str(uuid.uuid4()),
                "rule_code": "CERT-ISO9001",
                "rule_name": "ISO 9001",
                "rule_type": "CERTIFICATION_REQUIRED",
                "is_mandatory": True,
                "parameters": {"certification_name": "ISO-9001"},
            }
        ],
        "quotations": [
            {
                "vendor_id": vendor_a_id,
                "vendor_name": "AeroPrecision CNC",
                "base_price": "165000.00",
                "freight_cost": "2000.00",
                "insurance_cost": "500.00",
                "tax_amount": "8000.00",
                "discount_amount": "1000.00",
                "currency": "USD",
                "quoted_delivery_date": "2026-11-20",
                "incoterms": "DDP",
                "payment_terms": "Net 30",
                "warranty_months": 24,
            },
            {
                "vendor_id": vendor_b_id,
                "vendor_name": "Precision Fabworks",
                "base_price": "180000.00",
                "freight_cost": "3000.00",
                "insurance_cost": "600.00",
                "tax_amount": "9000.00",
                "discount_amount": "500.00",
                "currency": "USD",
                "quoted_delivery_date": "2026-11-25",
                "incoterms": "DDP",
                "payment_terms": "Net 30",
                "warranty_months": 12,
            },
        ],
    }

    # Step 1: Run graph until the interrupt gate
    interrupted_result = execute_evaluation(
        initial_state=initial_state,
        thread_id=thread_id,
        graph=graph,
    )

    # Verify that the workflow interrupted at approval_gate
    assert "__interrupt__" in interrupted_result
    assert interrupted_result["__interrupt__"][0].value["type"] == "PROCUREMENT_APPROVAL_REQUIRED"
    assert interrupted_result["status"] == "AWAITING_APPROVAL"
    assert "scorecard" in interrupted_result
    assert "decision_explanation" in interrupted_result
    assert len(interrupted_result["scorecard"]["scores"]) == 2
    assert interrupted_result["scorecard"]["recommended_vendor_id"] is not None

    # Step 2: Human Officer provides sign-off (Resume graph)
    approver_id = str(uuid.uuid4())
    approval_payload = {
        "action": "APPROVED",
        "comments": "Commercial terms and lead times verified. Award authorized.",
        "approver_user_id": approver_id,
    }

    resumed_result = resume_evaluation(
        thread_id=thread_id,
        approval_data=approval_payload,
        graph=graph,
    )

    # Verify finalization post-approval
    assert resumed_result["status"] == "APPROVED"
    assert resumed_result["approval_status"] == "APPROVED"
    assert resumed_result["approval_action"] == "APPROVED"
    assert resumed_result["approver_user_id"] == approver_id
    assert resumed_result["signature_hash"] is not None
    assert len(resumed_result["signature_hash"]) == 64


def test_procurement_graph_human_rejection():
    """Verify that human rejection transitions status to REJECTED."""
    checkpointer = MemorySaver()
    graph = build_procurement_graph(checkpointer=checkpointer)

    thread_id = f"test-eval-reject-{uuid.uuid4()}"
    initial_state: ProcurementEvaluationState = {
        "organization_id": str(uuid.uuid4()),
        "request_id": str(uuid.uuid4()),
        "evaluation_id": str(uuid.uuid4()),
        "thread_id": thread_id,
        "status": "INTAKE",
        "is_clarification_needed": False,
        "clarification_questions": [],
        "missing_fields": [],
        "raw_input": {
            "text": "Need 50 sensors. Budget is $50,000. Required delivery by 2026-11-15.",
            "budget_ceiling": 50000.00,
            "target_delivery_date": "2026-11-15",
            "currency": "USD",
        },
    }

    # Run to interrupt
    interrupted_result = execute_evaluation(
        initial_state=initial_state,
        thread_id=thread_id,
        graph=graph,
    )
    assert "__interrupt__" in interrupted_result

    # Reject
    resumed_result = resume_evaluation(
        thread_id=thread_id,
        approval_data={
            "action": "REJECTED",
            "comments": "Procurement request cancelled by department manager.",
            "approver_user_id": "mgr-999",
        },
        graph=graph,
    )

    assert resumed_result["status"] == "REJECTED"
    assert resumed_result["approval_action"] == "REJECTED"


def test_procurement_graph_incomplete_clarification_routing():
    """Verify that incomplete requirements halt at intake and do not run downstream evaluation."""
    checkpointer = MemorySaver()
    graph = build_procurement_graph(checkpointer=checkpointer)

    thread_id = f"test-eval-clarify-{uuid.uuid4()}"
    initial_state: ProcurementEvaluationState = {
        "organization_id": str(uuid.uuid4()),
        "request_id": str(uuid.uuid4()),
        "evaluation_id": str(uuid.uuid4()),
        "thread_id": thread_id,
        "status": "INTAKE",
        "is_clarification_needed": False,
        "clarification_questions": [],
        "missing_fields": [],
        "raw_input": {
            "text": "We need some parts urgently.",
            # Omit budget ceiling, target delivery date, item quantities
        },
    }

    result = execute_evaluation(
        initial_state=initial_state,
        thread_id=thread_id,
        graph=graph,
    )

    # Must be routed to END after intake without reaching approval interrupt
    assert "__interrupt__" not in result
    assert result["is_clarification_needed"] is True
    assert result["status"] == "AWAITING_CLARIFICATION"
    assert len(result["clarification_questions"]) > 0
    assert "scorecard" not in result
