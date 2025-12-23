"""Whisper inference stub.

Real implementation should load ONNX Whisper and stream partial/final transcripts.
This stub simulates streaming text for integration testing.
"""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator, Optional


class WhisperEngine:
    def __init__(self, model_path: Optional[str] = None, device: str = "auto") -> None:
        self.model_path = model_path
        self.device = device
        self._warmed = False

    async def warmup(self) -> None:
        # TODO: load ONNX model and tokenizer here
        await asyncio.sleep(0)
        self._warmed = True

    async def stream_transcript(self, meeting_id: str) -> AsyncGenerator[tuple[str, str], None]:
        """
        Yield tuples of (event_type, text), where event_type is "partial" or "final".
        This is a stub that emits deterministic dummy text.
        """
        counter = 0
        while True:
            counter += 1
            yield "partial", f"partial snippet {counter} for {meeting_id}"
            await asyncio.sleep(1.0)
            yield "final", f"final snippet {counter} for {meeting_id}"
            await asyncio.sleep(1.5)
