"""FastAPI router for procurement requisition headers and intake specifications."""

import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user_id, get_tenant_id
from app.agents.requirement_agent import RequirementAnalysisAgent
from app.schemas.spec import RawProcurementInput, ProcurementSpecResult

router = APIRouter()


class CreateProcurementRequestPayload(BaseModel):
    """Payload to initiate a new procurement request."""
    title: str
    description: str
    budget_ceiling: Optional[Decimal] = None
    target_delivery_date: Optional[str] = None
    currency: str = "USD"
    required_certifications: List[str] = Field(default_factory=list)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_procurement_request(
    payload: CreateProcurementRequestPayload,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Parse and create a structured procurement request."""
    raw_input = RawProcurementInput(
        text=payload.description,
        budget_ceiling=payload.budget_ceiling,
        currency=payload.currency,
        required_certifications=payload.required_certifications,
    )
    analysis: ProcurementSpecResult = RequirementAnalysisAgent.analyze(raw_input)

    request_id = uuid.uuid4()
    return {
        "id": request_id,
        "organization_id": tenant_id,
        "requester_id": current_user_id,
        "title": payload.title,
        "status": "DRAFT" if analysis.is_complete else "REQUIREMENT_CLARIFICATION",
        "analysis": analysis.model_dump(mode="json"),
    }
