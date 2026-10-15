"""Unit tests for Agent 9: Decision Coordinator."""

import uuid
from app.agents.coordinator_agent import DecisionCoordinator


def test_coordinator_lifecycle():
    """Verify coordinator starts evaluation, yields interrupt state, and resumes on approval."""
    coordinator = DecisionCoordinator()
    thread_id = f"coord-test-{uuid.uuid4()}"

    vendor_id = str(uuid.uuid4())
    candidate_vendors = [
        {
            "vendor_id": vendor_id,
            "vendor_name": "AeroTech Components",
            "certifications": ["ISO-9001"],
            "historical_orders_count": 10,
            "on_time_delivery_rate": 0.95,
            "defect_rate": 0.01,
            "spend_concentration_pct": 10.0,
        }
    ]

    # Start evaluation
    interrupted_state = coordinator.start_evaluation(
        raw_text="Procuring 200 units of titanium fittings. Budget is $150,000. Target date 2026-12-01.",
        organization_id=str(uuid.uuid4()),
        budget_ceiling=150000.00,
        target_delivery_date="2026-12-01",
        currency="USD",
        required_certifications=["ISO-9001"],
        candidate_vendors=candidate_vendors,
        thread_id=thread_id,
    )

    assert "__interrupt__" in interrupted_state
    assert interrupted_state["status"] == "AWAITING_APPROVAL"

    # Inspect checkpointed state
    snapshot = coordinator.get_evaluation_state(thread_id)
    assert snapshot["status"] == "AWAITING_APPROVAL"
    assert "scorecard" in snapshot

    # Resume with human approval
    final_state = coordinator.submit_human_approval(
        thread_id=thread_id,
        action="APPROVED",
        comments="Approved by procurement lead.",
        approver_user_id="lead-001",
    )

    assert final_state["status"] == "APPROVED"
    assert final_state["approval_action"] == "APPROVED"
    assert final_state["signature_hash"] is not None
