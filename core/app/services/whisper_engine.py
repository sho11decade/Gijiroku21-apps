"""Whisper inference wrapper with graceful fallback.

動作方針:
- GIJIROKU21_FAKE_ASR=1 → ダミー出力のみ
- GIJIROKU21_WHISPER_ONNX / core/models/whisper-small.onnx が存在し、tokenizer.json が
    読み込めれば onnxruntime + tokenizers による簡易グリーディデコードを行う。
- 依存欠如や推論エラー時は自動でダミーにフォールバックする。
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator, Optional, AsyncIterable, List, Dict, Any

import numpy as np

from core.app.models.transcript import TranscriptEvent


# Audio / feature constants aligned with Whisper defaults
SAMPLE_RATE = 16000
N_SAMPLES = SAMPLE_RATE * 30  # 30s context window
N_FFT = 400
HOP_LENGTH = 160
N_MELS = 80
MIN_PARTIAL_SAMPLES = SAMPLE_RATE * 2  # run partial after ~2s or more
LOG_MEL_EPS = 1e-10


class WhisperEngine:
    def __init__(self, model_path: Optional[str] = None, device: str = "auto") -> None:
        base_dir = Path(__file__).resolve().parents[3] / "core" / "models"
        default_model = base_dir / "whisper-small.onnx"
        default_tokenizer = base_dir / "tokenizer.json"

        self.model_path = model_path or os.getenv("GIJIROKU21_WHISPER_ONNX", str(default_model))
        self.tokenizer_path = os.getenv("GIJIROKU21_WHISPER_TOKENIZER", str(default_tokenizer))
        self.device = device
        self._warmed = False
        self._dummy = False
        self._session = None
        self._tokenizer = None
        self._input_names: List[str] = []
        self._output_names: List[str] = []
        self._features_input: Optional[str] = None
        self._decoder_input: Optional[str] = None
        self._logits_index: int = 0
        self._sot_token: Optional[int] = None
        self._eot_token: Optional[int] = None
        self._notimestamps_token: Optional[int] = None
        self._ja_token: Optional[int] = None
        self._pcm_buffer = np.zeros(0, dtype=np.float32)
        self._last_partial: Optional[str] = None

    async def warmup(self) -> None:
        if os.getenv("GIJIROKU21_FAKE_ASR", "0") == "1":
            self._dummy = True
            self._warmed = True
            return

        try:
            from tokenizers import Tokenizer  # type: ignore
            import onnxruntime as ort  # type: ignore

            if not self.model_path or not Path(self.model_path).exists():
                raise FileNotFoundError("ONNX model not found")
            if not self.tokenizer_path or not Path(self.tokenizer_path).exists():
                raise FileNotFoundError("tokenizer.json not found")

            providers = ["CPUExecutionProvider"]
            self._session = ort.InferenceSession(self.model_path, providers=providers)
            self._tokenizer = Tokenizer.from_file(str(self.tokenizer_path))

            self._input_names = [i.name for i in self._session.get_inputs()]
            self._output_names = [o.name for o in self._session.get_outputs()]
            # heuristic: first input -> features, second -> decoder tokens
            self._features_input = self._input_names[0] if self._input_names else None
            self._decoder_input = self._input_names[1] if len(self._input_names) > 1 else None
            self._logits_index = 0

            self._sot_token = self._tokenizer.token_to_id("<|startoftranscript|>")
            self._eot_token = self._tokenizer.token_to_id("<|endoftext|>")
            self._notimestamps_token = self._tokenizer.token_to_id("<|notimestamps|>")
            self._ja_token = self._tokenizer.token_to_id("<|ja|>")

            if not self._features_input or self._decoder_input is None:
                raise RuntimeError("Unexpected ONNX model inputs")

            self._dummy = False
            self._warmed = True
        except Exception:
            # Dependency missing or model unusable
            self._dummy = True
            self._warmed = True

    def _pcm_bytes_to_float(self, pcm: bytes) -> np.ndarray:
        data = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
        return data

    def _mel_filters(self) -> np.ndarray:
        # Port of Whisper mel filter creation (HTK scale)
        def hz_to_mel(f: float) -> float:
            return 2595.0 * np.log10(1.0 + f / 700.0)

        def mel_to_hz(m: float) -> float:
            return 700.0 * (10.0 ** (m / 2595.0) - 1.0)

        f_min = 0.0
        f_max = SAMPLE_RATE / 2
        mels = np.linspace(hz_to_mel(f_min), hz_to_mel(f_max), N_MELS + 2)
        hz = mel_to_hz(mels)
        bins = np.floor((N_FFT + 1) * hz / SAMPLE_RATE).astype(int)

        filters = np.zeros((N_MELS, N_FFT // 2 + 1))
        for i in range(N_MELS):
            start = int(bins[i])
            center = int(bins[i + 1])
            end = int(bins[i + 2])
            if center > start:
                filters[i, start:center] = (np.arange(start, center) - start) / (center - start)
            if end > center:
                filters[i, center:end] = (end - np.arange(center, end)) / (end - center)
        return filters

    def _log_mel_spectrogram(self, audio: np.ndarray) -> np.ndarray:
        audio = audio.flatten()
        # pad/trim to fixed context
        if len(audio) < N_SAMPLES:
            audio = np.pad(audio, (0, N_SAMPLES - len(audio)))
        elif len(audio) > N_SAMPLES:
            audio = audio[-N_SAMPLES:]

        window = np.hanning(N_FFT).astype(np.float32)
        frames = np.lib.stride_tricks.sliding_window_view(audio, N_FFT)[::HOP_LENGTH]
        if frames.shape[0] == 0:
            return np.zeros((1, N_MELS, 3000), dtype=np.float32)

        stft = np.fft.rfft(frames * window, n=N_FFT, axis=-1)
        magnitudes = np.abs(stft) ** 2
        mel_filters = self._mel_filters()
        mel_spec = magnitudes @ mel_filters.T
        log_mel = np.log10(np.maximum(mel_spec, LOG_MEL_EPS))
        log_mel = np.maximum(log_mel, log_mel.max() - 8.0)

        # ensure frame length fits model (crop/pad to 3000 frames)
        frames_target = 3000
        if log_mel.shape[0] < frames_target:
            pad_width = frames_target - log_mel.shape[0]
            pad_block = np.tile(log_mel[-1:], (pad_width, 1)) if log_mel.shape[0] > 0 else np.zeros((pad_width, N_MELS))
            log_mel = np.concatenate([log_mel, pad_block], axis=0)
        elif log_mel.shape[0] > frames_target:
            log_mel = log_mel[-frames_target:]

        log_mel = log_mel.T  # (n_mels, n_frames)
        return log_mel[np.newaxis, :, :].astype(np.float32)

    def _decode_logits(self, tokens: List[int]) -> str:
        if not self._tokenizer:
            return ""
        try:
            return self._tokenizer.decode(tokens, skip_special_tokens=True)
        except Exception:
            return ""

    def _greedy_decode(self, features: np.ndarray, max_steps: int = 64) -> str:
        if not self._session or self._features_input is None or self._decoder_input is None:
            return ""

        init_tokens = [t for t in [self._sot_token, self._ja_token, self._notimestamps_token] if t is not None]
        if not init_tokens:
            return ""

        decoder_tokens = init_tokens.copy()
        for _ in range(max_steps):
            inputs: Dict[str, Any] = {
                self._features_input: features,
                self._decoder_input: np.array([decoder_tokens], dtype=np.int64),
            }
            outputs = self._session.run(None, inputs)
            logits = outputs[self._logits_index]
            next_token = int(np.argmax(logits[0, -1]))
            decoder_tokens.append(next_token)
            if self._eot_token is not None and next_token == self._eot_token:
                break

        return self._decode_logits(decoder_tokens)

    async def run_from_pcm_stream(
        self, meeting_id: str, pcm_stream: AsyncIterable[Optional[bytes]]
    ) -> AsyncGenerator[TranscriptEvent, None]:
        """Consume PCM stream and emit partial/final events."""

        self._pcm_buffer = np.zeros(0, dtype=np.float32)
        self._last_partial = None

        if self._dummy:
            counter = 0
            while True:
                counter += 1
                yield TranscriptEvent(type="partial", text=f"partial snippet {counter} for {meeting_id}")
                await asyncio.sleep(1.0)
                yield TranscriptEvent(type="final", text=f"final snippet {counter} for {meeting_id}")
                await asyncio.sleep(1.5)

        async for chunk in pcm_stream:
            if chunk:
                self._pcm_buffer = np.concatenate([self._pcm_buffer, self._pcm_bytes_to_float(chunk)])
                if self._pcm_buffer.shape[0] > N_SAMPLES:
                    self._pcm_buffer = self._pcm_buffer[-N_SAMPLES:]

            should_decode = chunk is None or self._pcm_buffer.shape[0] >= MIN_PARTIAL_SAMPLES
            if not should_decode or self._pcm_buffer.shape[0] == 0:
                continue

            try:
                features = self._log_mel_spectrogram(self._pcm_buffer)
                text = self._greedy_decode(features)
            except Exception:
                text = ""

            if text and text != self._last_partial:
                self._last_partial = text
                yield TranscriptEvent(type="partial", text=text)

        # end-of-stream final emit
        if self._pcm_buffer.shape[0] > 0:
            try:
                features = self._log_mel_spectrogram(self._pcm_buffer)
                text = self._greedy_decode(features)
            except Exception:
                text = None

            if text:
                yield TranscriptEvent(type="final", text=text)
