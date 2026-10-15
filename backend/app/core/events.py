"""Event streaming and Pub/Sub broadcaster for real-time node state transitions."""

import asyncio
import json
from collections import defaultdict
from typing import AsyncGenerator, Dict, List, Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("app.core.events")


class EventBroadcaster:
    """Manages Server-Sent Events (SSE) broadcasting with Redis Pub/Sub and in-memory fallback."""

    def __init__(self):
        self._memory_subscribers: Dict[str, List[asyncio.Queue]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def broadcast(self, channel: str, event_type: str, payload: dict) -> None:
        """Publish an event to all subscribers listening on a specific thread or topic."""
        message = {
            "event": event_type,
            "data": payload,
        }
        json_data = json.dumps(message)
        formatted_sse = f"event: {event_type}\ndata: {json_data}\n\n"

        async with self._lock:
            queues = self._memory_subscribers.get(channel, [])
            for q in list(queues):
                try:
                    q.put_nowait(formatted_sse)
                except asyncio.QueueFull:
                    logger.warning("Subscriber queue full for channel %s, dropping event", channel)

    async def subscribe(self, channel: str) -> AsyncGenerator[str, None]:
        """Subscribe to SSE events for a specific evaluation thread."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._memory_subscribers[channel].append(queue)

        try:
            # Yield initial connection heartbeat
            yield f"event: connected\ndata: {json.dumps({'status': 'connected', 'channel': channel})}\n\n"
            while True:
                data = await queue.get()
                yield data
        finally:
            async with self._lock:
                if queue in self._memory_subscribers[channel]:
                    self._memory_subscribers[channel].remove(queue)
                if not self._memory_subscribers[channel]:
                    del self._memory_subscribers[channel]


broadcaster = EventBroadcaster()
