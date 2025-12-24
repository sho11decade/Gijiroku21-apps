"""Whisper inference wrapper with graceful fallback to dummy mode.

動作方針:
- GIJIROKU21_FAKE_ASR=1 → ダミー出力のみ
- GIJIROKU21_WHISPER_ONNX で指定された ONNX モデルが存在し読み込めれば
    onnxruntime セッションを初期化（CPUExecutionProvider 優先）。失敗時はダミー。

現時点では実デコードは未実装だが、モデルがロードできた場合は "model-loaded"
ラベル付きで partial/final を返し、ダミー時は従来の固定文を返す。
今後、audio_capture から PCM チャンクを受け取り実推論する際の土台となる。
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator, Optional, Tuple, AsyncIterable


class WhisperEngine:
    def __init__(self, model_path: Optional[str] = None, device: str = "auto") -> None:
        self.model_path = model_path or os.getenv("GIJIROKU21_WHISPER_ONNX", "")
        self.device = device
        self._warmed = False
        self._dummy = False
        self._session = None

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

            providers = ["CPUExecutionProvider"]
            self._session = ort.InferenceSession(self.model_path, providers=providers)
            self._dummy = False
            self._warmed = True
        except Exception:
            self._dummy = True
            self._warmed = True

    async def run_from_pcm_stream(
        self, meeting_id: str, pcm_stream: AsyncIterable[Optional[bytes]]
    ) -> AsyncGenerator[Tuple[str, str], None]:
        """Consume PCM stream and emit partial/final events.

        現時点ではダミー/簡易実装:
        - dummy: タイマーで partial/final を送る（PCMは無視）
        - model-loaded: PCMチャンクを受け取りつつ、受信回数をカウントして partial/final を生成
          ※実デコードは未実装。今後 tokenizer + logits -> text デコードを組み込む。
        """

        if self._dummy:
            counter = 0
            while True:
                counter += 1
                yield "partial", f"partial snippet {counter} for {meeting_id}"
                await asyncio.sleep(1.0)
                yield "final", f"final snippet {counter} for {meeting_id}"
                await asyncio.sleep(1.5)

        # model loaded path (still stub decoding)
        counter = 0
        async for chunk in pcm_stream:
            counter += 1
            if chunk is None:
                # heartbeat, continue
                continue
            # In future: feed chunk into model to produce partial/final.
            yield "partial", f"partial (model-loaded) {counter} for {meeting_id}"
            yield "final", f"final (model-loaded) {counter} for {meeting_id}"
