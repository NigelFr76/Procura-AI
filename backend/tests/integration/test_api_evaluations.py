"""Integration tests for FastAPI evaluation and negotiation REST endpoints."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_evaluation_end_to_end_flow(async_client: AsyncClient):
    """Test full API lifecycle: create evaluation, poll status, and submit human approval."""
    thread_id = f"api-test-{uuid.uuid4()}"
    vendor_id = str(uuid.uuid4())

    payload = {
        "text": "Need 500 titanium aircraft structural bolts. Budget is $150,000 USD. Required delivery by 2026-12-15.",
        "budget_ceiling": 150000.00,
        "target_delivery_date": "2026-12-15",
        "currency": "USD",
        "required_certifications": ["ISO-9001"],
        "candidate_vendors": [
            {
                "vendor_id": vendor_id,
                "vendor_name": "Titan Precision Fasteners",
                "certifications": ["ISO-9001"],
                "historical_orders_count": 10,
                "on_time_delivery_rate": 0.96,
                "defect_rate": 0.008,
                "spend_concentration_pct": 12.0,
            }
        ],
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
                "vendor_id": vendor_id,
                "vendor_name": "Titan Precision Fasteners",
                "base_price": "125000.00",
                "freight_cost": "2000.00",
                "insurance_cost": "500.00",
                "tax_amount": "6000.00",
                "discount_amount": "1000.00",
                "currency": "USD",
                "quoted_delivery_date": "2026-12-01",
                "incoterms": "DDP",
                "payment_terms": "Net 30",
                "warranty_months": 12,
            }
        ],
        "thread_id": thread_id,
    }

    # 1. Start Evaluation
    start_resp = await async_client.post("/api/v1/evaluations", json=payload)
    assert start_resp.status_code == 201
    start_data = start_resp.json()
    assert start_data["thread_id"] == thread_id
    assert start_data["status"] == "AWAITING_APPROVAL"
    assert start_data["scorecard"] is not None
    assert start_data["decision_explanation"] is not None

    # 2. Get Evaluation Status
    get_resp = await async_client.get(f"/api/v1/evaluations/{thread_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["thread_id"] == thread_id
    assert get_data["status"] == "AWAITING_APPROVAL"

    # 3. Submit Human Officer Approval
    approval_resp = await async_client.post(
        f"/api/v1/evaluations/{thread_id}/approval",
        json={
            "action": "APPROVED",
            "comments": "Commercial terms validated. Award approved.",
        },
    )
    assert approval_resp.status_code == 200
    approval_data = approval_resp.json()
    assert approval_data["status"] == "APPROVED"
    assert approval_data["approval_action"] == "APPROVED"
    assert approval_data["signature_hash"] is not None
    assert len(approval_data["signature_hash"]) == 64


@pytest.mark.asyncio
async def test_api_negotiation_simulation(async_client: AsyncClient):
    """Test negotiation counteroffer simulation REST endpoint."""
    vendor_id = str(uuid.uuid4())
    payload = {
        "vendor_id": vendor_id,
        "vendor_name": "Aero Castings Ltd",
        "quoted_base_price": 250000.00,
        "quoted_delivery_days": 40,
        "quoted_payment_terms": "Net 30",
        "quoted_warranty_months": 12,
        "target_price_discount_pct": 10.0,
        "target_payment_terms": "Net 60",
        "vendor_elasticity_score": 0.7,
        "cost_floor_pct": 82.0,
    }

    resp = await async_client.post("/api/v1/negotiations/simulate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["vendor_id"] == vendor_id
    assert len(data["rounds"]) == 3
    assert float(data["expected_final_price"]) < 250000.00
    assert data["is_hypothetical_simulation"] is True


@pytest.mark.asyncio
async def test_api_create_procurement_request(async_client: AsyncClient):
    """Test procurement requisition creation endpoint with Agent 1 intake."""
    payload = {
        "title": "Avionics Sensors Bulk Order",
        "description": "Need 200 temperature sensor modules. Budget is $80,000 USD. Required delivery by 2026-11-30.",
        "budget_ceiling": 80000.00,
        "currency": "USD",
        "required_certifications": ["ISO-9001"],
    }

    resp = await async_client.post("/api/v1/requests", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["title"] == "Avionics Sensors Bulk Order"
    assert data["analysis"]["is_complete"] is True
