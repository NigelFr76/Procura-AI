"""FastAPI router for real-time Server-Sent Events (SSE) streaming."""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.events import broadcaster

router = APIRouter()


@router.get("/stream/{thread_id}")
async def stream_evaluation_events(thread_id: str):
    """Subscribe to real-time agent execution events and node transitions."""
    return StreamingResponse(
        broadcaster.subscribe(thread_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
