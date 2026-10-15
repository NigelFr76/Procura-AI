"""Unit tests for AuditService cryptographic ledger chaining and tamper detection."""

from app.services.audit.audit_service import AuditAction, AuditService


def test_audit_chain_creation_and_integrity():
    tenant_id = "test-tenant-audit-01"
    AuditService.clear_ledger(tenant_id)

    # 1. Record series of events
    r1 = AuditService.record_event(
        tenant_id=tenant_id,
        user_id="user-01",
        action=AuditAction.EVALUATION_STARTED,
        payload={"budget": 100000},
    )
    assert r1.previous_hash == AuditService.GENESIS_HASH

    r2 = AuditService.record_event(
        tenant_id=tenant_id,
        user_id="user-02",
        action=AuditAction.EVALUATION_SCORED,
        payload={"winner": "Apex Corp", "score": 92.5},
    )
    assert r2.previous_hash == r1.current_hash

    r3 = AuditService.record_event(
        tenant_id=tenant_id,
        user_id="officer-01",
        action=AuditAction.HITL_APPROVAL_GRANTED,
        payload={"status": "APPROVED", "signature": "sha256:abc"},
    )
    assert r3.previous_hash == r2.current_hash

    # 2. Verify unbroken chain
    ledger = AuditService.get_ledger(tenant_id)
    assert len(ledger) == 3
    is_valid, error = AuditService.verify_chain_integrity(ledger)
    assert is_valid is True
    assert error is None


def test_tamper_detection_on_modified_payload():
    tenant_id = "test-tenant-tamper-02"
    AuditService.clear_ledger(tenant_id)

    AuditService.record_event(
        tenant_id=tenant_id,
        user_id="user-01",
        action=AuditAction.EVALUATION_STARTED,
        payload={"budget": 50000},
    )
    AuditService.record_event(
        tenant_id=tenant_id,
        user_id="user-02",
        action=AuditAction.EVALUATION_SCORED,
        payload={"winner": "Vendor A"},
    )

    ledger = AuditService.get_ledger(tenant_id)

    # Malicious actor tampers with payload in the middle of the chain
    ledger[1].payload["winner"] = "Fraudulent Vendor"

    # Integrity verification must catch the tamper
    is_valid, error = AuditService.verify_chain_integrity(ledger)
    assert is_valid is False
    assert "Tampered record at index 1" in error


def test_tamper_detection_on_broken_hash_link():
    tenant_id = "test-tenant-tamper-03"
    AuditService.clear_ledger(tenant_id)

    AuditService.record_event(
        tenant_id=tenant_id,
        user_id="user-01",
        action=AuditAction.EVALUATION_STARTED,
        payload={"step": 1},
    )
    AuditService.record_event(
        tenant_id=tenant_id,
        user_id="user-02",
        action=AuditAction.DOCUMENT_INGESTED,
        payload={"doc": "quote.pdf"},
    )

    ledger = AuditService.get_ledger(tenant_id)

    # Malicious actor corrupts previous_hash
    ledger[1].previous_hash = "deadbeef" * 8

    is_valid, error = AuditService.verify_chain_integrity(ledger)
    assert is_valid is False
    assert "Chain broken at index 1" in error
