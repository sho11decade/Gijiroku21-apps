import asyncio
from typing import AsyncGenerator

from core.app.models.transcript import TranscriptEvent

_queue: asyncio.Queue[TranscriptEvent] = asyncio.Queue()


async def publish(event: TranscriptEvent) -> None:
    await _queue.put(event)


async def stream_events(heartbeat_interval: float = 5.0) -> AsyncGenerator[TranscriptEvent, None]:
    # Send initial ready event
    yield TranscriptEvent(type="status", status="stream_ready")

    while True:
        try:
            event = await asyncio.wait_for(_queue.get(), timeout=heartbeat_interval)
            yield event
        except asyncio.TimeoutError:
            yield TranscriptEvent(type="status", status="heartbeat")
