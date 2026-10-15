"""FastAPI router for What-If scenario simulations and differential analysis."""

import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, status

from app.api.deps import get_tenant_id
from app.agents.scenario_agent import ScenarioSimulationAgent
from app.schemas.scenario import ScenarioRunInput, ScenarioRunResult

router = APIRouter()


@router.post("/simulate", response_model=ScenarioRunResult, status_code=status.HTTP_200_OK)
async def simulate_scenario(
    payload: ScenarioRunInput,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
) -> ScenarioRunResult:
    """Execute What-If scenario simulation against an immutable baseline evaluation."""
    return ScenarioSimulationAgent.run_simulation(payload)
