"""API v1 router aggregating all modular endpoint controllers."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    documents,
    evaluations,
    events,
    negotiations,
    requests,
    scenarios,
)

api_router = APIRouter()

api_router.include_router(evaluations.router, prefix="/evaluations", tags=["Evaluations"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["Scenarios"])
api_router.include_router(negotiations.router, prefix="/negotiations", tags=["Negotiations"])
api_router.include_router(requests.router, prefix="/requests", tags=["Requests"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(events.router, prefix="/events", tags=["Events"])
