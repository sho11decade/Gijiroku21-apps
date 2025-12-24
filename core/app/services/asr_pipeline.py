"""Dummy ASR pipeline that publishes transcript events.

This is a placeholder to be replaced with real audio->text processing. It simulates
partial/final events while recording is active.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from core.app.models.transcript import TranscriptEvent
from core.app.services.whisper_engine import WhisperEngine
from core.app.utils import transcript_stream
from core.app.utils import pcm_queue

_task: Optional[asyncio.Task] = None
_engine: Optional[WhisperEngine] = None


async def _ensure_engine() -> WhisperEngine:
    global _engine
    if _engine is None:
        _engine = WhisperEngine()
        await _engine.warmup()
    return _engine


async def _runner(meeting_id: str) -> None:
    engine = await _ensure_engine()
    await transcript_stream.publish(TranscriptEvent(type="status", status="asr_started"))
    try:
        async for event in engine.run_from_pcm_stream(meeting_id, pcm_queue.stream()):
            await transcript_stream.publish(event)
    except asyncio.CancelledError:
        # Graceful shutdown
        await transcript_stream.publish(TranscriptEvent(type="status", status="asr_stopped"))
        raise


aSYNC_START_ERR = "ASR pipeline already running"


async def start(meeting_id: str) -> None:
    global _task
    if _task and not _task.done():
        raise RuntimeError(aSYNC_START_ERR)
    pcm_queue.reset()
    transcript_stream.reset_queue()
    _task = asyncio.create_task(_runner(meeting_id))


async def stop() -> None:
    global _task
    pcm_queue.close()
    if _task and not _task.done():
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
    _task = None
