"""FastAPI router for supplier counteroffer and negotiation simulations."""

import uuid
from fastapi import APIRouter, Depends, status

from app.api.deps import get_tenant_id
from app.agents.negotiation_agent import NegotiationSimulationAgent
from app.schemas.negotiation import NegotiationSimInput, NegotiationSimResult

router = APIRouter()


@router.post("/simulate", response_model=NegotiationSimResult, status_code=status.HTTP_200_OK)
async def simulate_negotiation(
    payload: NegotiationSimInput,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
) -> NegotiationSimResult:
    result = NegotiationSimulationAgent.simulate(payload)

    from app.services.audit.audit_service import AuditAction, AuditService
    AuditService.record_event(
        tenant_id=str(tenant_id),
        user_id="procurement-buyer",
        action=AuditAction.NEGOTIATION_COMPLETED,
        payload={
            "vendor_name": payload.vendor_name,
            "target_price_discount_pct": payload.target_price_discount_pct,
            "projected_savings_pct": result.projected_savings_pct,
        },
    )

    return result
