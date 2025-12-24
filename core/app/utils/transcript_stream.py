import asyncio
from typing import AsyncGenerator

from core.app.models.transcript import TranscriptEvent

_queue: asyncio.Queue[TranscriptEvent] = asyncio.Queue()
_closed = False


async def publish(event: TranscriptEvent) -> None:
    if _closed:
        return
    await _queue.put(event)


def reset_queue() -> None:
    """Drop all pending events (useful when starting a new recording)."""
    global _closed
    _closed = False
    while not _queue.empty():
        try:
            _queue.get_nowait()
        except asyncio.QueueEmpty:
            break


def close_queue() -> None:
    """Mark queue closed; further publish calls are ignored."""
    global _closed
    _closed = True


async def stream_events(heartbeat_interval: float = 5.0) -> AsyncGenerator[TranscriptEvent, None]:
    # Send initial ready event
    yield TranscriptEvent(type="status", status="stream_ready")

    while True:
        try:
            event = await asyncio.wait_for(_queue.get(), timeout=heartbeat_interval)
            yield event
        except asyncio.TimeoutError:
            yield TranscriptEvent(type="status", status="heartbeat")
