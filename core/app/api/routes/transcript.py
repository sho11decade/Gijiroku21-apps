from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from core.app.models.transcript import TranscriptEvent
from core.app.utils.sse import format_sse
from core.app.utils.transcript_stream import stream_events

router = APIRouter(prefix="/transcript", tags=["transcript"])

@router.get("/stream")
async def transcript_stream() -> StreamingResponse:
    async def _generator() -> AsyncGenerator[bytes, None]:
        async for event in stream_events():
            yield format_sse(event.model_dump(), event=event.type).encode()

    return StreamingResponse(_generator(), media_type="text/event-stream")
