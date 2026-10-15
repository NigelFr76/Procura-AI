"""Integration tests for security headers middleware and audit API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.audit.audit_service import AuditService


@pytest.mark.asyncio
async def test_security_headers_present_on_all_responses():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")

        assert response.status_code == 200
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert "Strict-Transport-Security" in response.headers
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


@pytest.mark.asyncio
async def test_audit_verification_endpoint():
    tenant_id = "00000000-0000-0000-0000-000000000001"
    AuditService.clear_ledger(tenant_id)

    # Record test event
    AuditService.record_event(
        tenant_id=tenant_id,
        user_id="test-officer",
        action="EVALUATION_STARTED",
        payload={"rfp_title": "Test Integration RFP"},
    )

    headers = {"X-Tenant-ID": tenant_id}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Fetch audit logs
        log_res = await client.get("/api/v1/audit/logs", headers=headers)
        assert log_res.status_code == 200
        logs = log_res.json()
        assert len(logs) >= 1
        assert logs[0]["action"] == "EVALUATION_STARTED"

        # 2. Verify ledger integrity
        verify_res = await client.get("/api/v1/audit/verify", headers=headers)
        assert verify_res.status_code == 200
        verify_data = verify_res.json()
        assert verify_data["is_integrity_valid"] is True
        assert verify_data["total_records"] >= 1
