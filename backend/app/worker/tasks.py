"""Background worker tasks for asynchronous evaluation execution."""

import asyncio
from typing import Any, Dict, Optional
from app.agents.coordinator_agent import coordinator
from app.core.events import broadcaster
from app.core.logging import get_logger

logger = get_logger("app.worker.tasks")


async def run_async_evaluation_task(
    thread_id: str,
    raw_text: str,
    organization_id: str,
    budget_ceiling: Optional[float] = None,
    target_delivery_date: Optional[str] = None,
    currency: str = "USD",
    candidate_vendors: Optional[list] = None,
    compliance_rules: Optional[list] = None,
    quotations: Optional[list] = None,
) -> Dict[str, Any]:
    """Execute LangGraph evaluation in async background context and stream progress."""
    logger.info("Executing async evaluation worker task for thread %s...", thread_id)
    
    await broadcaster.broadcast(
        channel=thread_id,
        event_type="evaluation.worker_started",
        payload={"thread_id": thread_id, "status": "RUNNING"},
    )

    loop = asyncio.get_running_loop()
    state = await loop.run_in_executor(
        None,
        lambda: coordinator.start_evaluation(
            raw_text=raw_text,
            organization_id=organization_id,
            budget_ceiling=budget_ceiling,
            target_delivery_date=target_delivery_date,
            currency=currency,
            candidate_vendors=candidate_vendors,
            compliance_rules=compliance_rules,
            quotations=quotations,
            thread_id=thread_id,
        ),
    )

    await broadcaster.broadcast(
        channel=thread_id,
        event_type="evaluation.worker_finished",
        payload={"thread_id": thread_id, "status": state.get("status")},
    )

    return state
