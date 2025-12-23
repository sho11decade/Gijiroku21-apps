"""Whisper inference wrapper with graceful fallback to dummy mode.

This module attempts to load an ONNX Whisper model if available. When unavailable
or when GIJIROKU21_FAKE_ASR=1 is set, it emits dummy partial/final text to keep
the pipeline alive without external downloads.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator, Optional, Tuple


class WhisperEngine:
    def __init__(self, model_path: Optional[str] = None, device: str = "auto") -> None:
        self.model_path = model_path or os.getenv("GIJIROKU21_WHISPER_ONNX", "")
        self.device = device
        self._warmed = False
        self._dummy = False

    async def warmup(self) -> None:
        if os.getenv("GIJIROKU21_FAKE_ASR", "0") == "1":
            self._dummy = True
            self._warmed = True
            return

        if not self.model_path or not Path(self.model_path).exists():
            # model not available, fallback to dummy
            self._dummy = True
            self._warmed = True
            return

        try:
            import onnxruntime as ort  # type: ignore

            # Here we only validate the session can be created; actual inference is TODO
            ort.InferenceSession(self.model_path, providers=["CPUExecutionProvider"])
            self._dummy = False
            self._warmed = True
        except Exception:
            self._dummy = True
            self._warmed = True

    async def stream_transcript(self, meeting_id: str) -> AsyncGenerator[Tuple[str, str], None]:
        """Yield tuples of (event_type, text). In dummy mode emits synthetic text."""
        counter = 0
        while True:
            counter += 1
            if self._dummy:
                yield "partial", f"partial snippet {counter} for {meeting_id}"
                await asyncio.sleep(1.0)
                yield "final", f"final snippet {counter} for {meeting_id}"
                await asyncio.sleep(1.5)
            else:
                # Placeholder for real inference loop: feed audio chunks and produce partial/final
                # This branch needs implementing once audio buffering + tokenizer are wired.
                await asyncio.sleep(1.0)
                yield "partial", f"partial (stub real) {counter} for {meeting_id}"
                await asyncio.sleep(0.5)
                yield "final", f"final (stub real) {counter} for {meeting_id}"
