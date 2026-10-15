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
    result = ScenarioSimulationAgent.run_simulation(payload)

    from app.services.audit.audit_service import AuditAction, AuditService
    AuditService.record_event(
        tenant_id=str(tenant_id),
        user_id="scenario-analyst",
        action=AuditAction.SCENARIO_SIMULATED,
        payload={
            "scenario_name": payload.scenario_name,
            "baseline_evaluation_id": payload.baseline_evaluation_id,
            "winner_displaced": result.winner_displaced,
            "new_winner_name": result.new_winner_name,
        },
    )

    return result
