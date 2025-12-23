"""Audio capture service (ダミー実装).

sounddevice/pyaudio への置き換え前提で、現時点では録音中フラグ管理のみ行い、
stop 時に希望されれば 1 秒分の無音 WAV を生成する。
"""

from __future__ import annotations

import wave
from pathlib import Path
from threading import Lock
from typing import Optional

from core.app.utils import paths

SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2  # bytes per sample (16-bit PCM)

_lock = Lock()
_active = False
_output_path: Optional[Path] = None


def start_capture(meeting_id: str, save_audio: bool) -> None:
    """録音開始フック。重複開始を防ぎ、保存が必要な場合は出力パスを保持する。"""
    global _active, _output_path
    with _lock:
        if _active:
            raise RuntimeError("Audio capture already active")
        _active = True
        _output_path = None
        if save_audio:
            meeting_dir = paths.meeting_dir(meeting_id)
            meeting_dir.mkdir(parents=True, exist_ok=True)
            _output_path = meeting_dir / "audio.wav"


def _write_silence(path: Path, seconds: float = 1.0) -> None:
    frames = int(SAMPLE_RATE * seconds)
    silence = (b"\x00" * SAMPLE_WIDTH) * frames
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(silence)


def stop_capture() -> None:
    """録音停止フック。必要に応じて無音WAVを出力し、状態をリセットする。"""
    global _active, _output_path
    with _lock:
        if not _active:
            raise RuntimeError("Audio capture not active")
        if _output_path:
            _write_silence(_output_path)
        _active = False
        _output_path = None
