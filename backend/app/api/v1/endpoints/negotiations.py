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
    """Simulate multi-round vendor counteroffers within bounded elasticity frontiers."""
    return NegotiationSimulationAgent.simulate(payload)
