"""FastAPI router for tamper-evident cryptographic audit logs and verification."""

import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status

from app.api.deps import get_tenant_id
from app.services.audit.audit_service import AuditRecord, AuditService

router = APIRouter()


@router.get("/logs", response_model=List[AuditRecord], status_code=status.HTTP_200_OK)
async def get_audit_logs(
    tenant_id: uuid.UUID = Depends(get_tenant_id),
) -> List[AuditRecord]:
    """Retrieve the cryptographically linked audit chain for the active tenant."""
    return AuditService.get_ledger(str(tenant_id))


@router.get("/verify", status_code=status.HTTP_200_OK)
async def verify_audit_ledger(
    tenant_id: uuid.UUID = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Verify unbroken cryptographic SHA-256 integrity of the tenant's audit ledger."""
    records = AuditService.get_ledger(str(tenant_id))
    is_valid, error = AuditService.verify_chain_integrity(records)

    head_hash = records[-1].current_hash if records else AuditService.GENESIS_HASH

    return {
        "tenant_id": str(tenant_id),
        "total_records": len(records),
        "chain_head_hash": head_hash,
        "is_integrity_valid": is_valid,
        "verification_error": error,
    }
