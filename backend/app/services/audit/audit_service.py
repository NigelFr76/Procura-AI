"""Tamper-Evident Cryptographic Audit Logging Service with SHA-256 Hash Chaining."""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class AuditAction(str, Enum):
    """Standardized audit actions across procurement platform lifecycle."""
    EVALUATION_STARTED = "EVALUATION_STARTED"
    REQUIREMENT_PARSED = "REQUIREMENT_PARSED"
    DOCUMENT_INGESTED = "DOCUMENT_INGESTED"
    PROMPT_INJECTION_FLAGGED = "PROMPT_INJECTION_FLAGGED"
    EVALUATION_SCORED = "EVALUATION_SCORED"
    HITL_APPROVAL_GRANTED = "HITL_APPROVAL_GRANTED"
    HITL_REJECTION_ISSUED = "HITL_REJECTION_ISSUED"
    SCENARIO_SIMULATED = "SCENARIO_SIMULATED"
    NEGOTIATION_COMPLETED = "NEGOTIATION_COMPLETED"


class AuditRecord(BaseModel):
    """Immutable audit ledger block with forward and backward cryptographic links."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tenant_id: str
    user_id: str
    action: str
    payload: Dict[str, Any]
    previous_hash: str
    current_hash: str


class AuditService:
    """Enterprise Audit Service guaranteeing non-repudiation and cryptographic integrity."""

    # In-memory ledger storage (scoped by tenant_id)
    _ledger: Dict[str, List[AuditRecord]] = {}
    GENESIS_HASH: str = "0" * 64

    @classmethod
    def compute_record_hash(
        cls,
        event_id: str,
        timestamp: str,
        tenant_id: str,
        user_id: str,
        action: str,
        payload: Dict[str, Any],
        previous_hash: str,
    ) -> str:
        """Compute authoritative SHA-256 hash for an audit ledger entry."""
        serialized_payload = json.dumps(payload, sort_keys=True, default=str)
        raw_token = f"{event_id}|{timestamp}|{tenant_id}|{user_id}|{action}|{serialized_payload}|{previous_hash}"
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @classmethod
    def record_event(
        cls,
        tenant_id: str,
        user_id: str,
        action: AuditAction | str,
        payload: Dict[str, Any],
    ) -> AuditRecord:
        """Append an immutable cryptographically chained audit record to the tenant ledger."""
        action_str = action.value if isinstance(action, AuditAction) else str(action)
        if tenant_id not in cls._ledger:
            cls._ledger[tenant_id] = []

        tenant_chain = cls._ledger[tenant_id]
        prev_hash = tenant_chain[-1].current_hash if len(tenant_chain) > 0 else cls.GENESIS_HASH

        e_id = str(uuid.uuid4())
        ts = datetime.now(timezone.utc).isoformat()
        curr_hash = cls.compute_record_hash(
            event_id=e_id,
            timestamp=ts,
            tenant_id=tenant_id,
            user_id=user_id,
            action=action_str,
            payload=payload,
            previous_hash=prev_hash,
        )

        record = AuditRecord(
            event_id=e_id,
            timestamp=ts,
            tenant_id=tenant_id,
            user_id=user_id,
            action=action_str,
            payload=payload,
            previous_hash=prev_hash,
            current_hash=curr_hash,
        )

        tenant_chain.append(record)
        return record

    @classmethod
    def get_ledger(cls, tenant_id: str) -> List[AuditRecord]:
        """Retrieve the immutable audit chain for a specific tenant."""
        return cls._ledger.get(tenant_id, [])

    @classmethod
    def clear_ledger(cls, tenant_id: Optional[str] = None) -> None:
        """Reset ledger (for testing and isolation)."""
        if tenant_id:
            cls._ledger.pop(tenant_id, None)
        else:
            cls._ledger.clear()

    @classmethod
    def verify_chain_integrity(cls, records: List[AuditRecord]) -> Tuple[bool, Optional[str]]:
        """Verify unbroken cryptographic integrity across an audit chain.
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_explanation)
        """
        if not records:
            return True, None

        for idx, rec in enumerate(records):
            # 1. Check previous hash continuity
            expected_prev_hash = cls.GENESIS_HASH if idx == 0 else records[idx - 1].current_hash
            if rec.previous_hash != expected_prev_hash:
                return (
                    False,
                    f"Chain broken at index {idx}: previous_hash '{rec.previous_hash}' does not match "
                    f"prior record hash '{expected_prev_hash}'.",
                )

            # 2. Recompute current hash to detect payload tampering
            recomputed = cls.compute_record_hash(
                event_id=rec.event_id,
                timestamp=rec.timestamp,
                tenant_id=rec.tenant_id,
                user_id=rec.user_id,
                action=rec.action,
                payload=rec.payload,
                previous_hash=rec.previous_hash,
            )
            if recomputed != rec.current_hash:
                return (
                    False,
                    f"Tampered record at index {idx}: recomputed hash '{recomputed}' does not match "
                    f"recorded hash '{rec.current_hash}'.",
                )

        return True, None
