"""Audio capture service.

sounddevice が利用可能ならマイクをキャプチャし、save_audio=True なら WAV に保存。
利用不可または GIJIROKU21_FAKE_AUDIO=1 の場合はダミー動作で無音WAVのみ書き出す。
"""

from __future__ import annotations

import os
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
_stream = None
_mode = "dummy"  # dummy | sounddevice


def _write_silence(path: Path, seconds: float = 1.0) -> None:
    frames = int(SAMPLE_RATE * seconds)
    silence = (b"\x00" * SAMPLE_WIDTH) * frames
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(silence)


def _start_sounddevice(target_path: Optional[Path]) -> None:
    global _stream
    try:
        import sounddevice as sd  # type: ignore
    except Exception:
        raise RuntimeError("sounddevice not available")

    wav_handle = None
    if target_path:
        wav_handle = wave.open(str(target_path), "wb")
        wav_handle.setnchannels(CHANNELS)
        wav_handle.setsampwidth(SAMPLE_WIDTH)
        wav_handle.setframerate(SAMPLE_RATE)

    def _callback(indata, frames, time, status):  # type: ignore[override]
        if status and wav_handle:
            # We ignore status for now; could log
            pass
        if wav_handle:
            wav_handle.writeframes(indata.tobytes())

    _stream = sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=0,
        dtype="int16",
        channels=CHANNELS,
        callback=_callback,
    )
    _stream.start()

    def _finalize():
        if wav_handle:
            wav_handle.close()

    _stream._finalize = _finalize  # type: ignore[attr-defined]


def _stop_sounddevice():
    global _stream
    if _stream:
        try:
            _stream.stop()
            if hasattr(_stream, "_finalize"):
                _stream._finalize()  # type: ignore[attr-defined]
        finally:
            _stream = None


def start_capture(meeting_id: str, save_audio: bool) -> None:
    """録音開始。sounddeviceがなければダミーにフォールバック。"""
    global _active, _output_path, _mode
    with _lock:
        if _active:
            raise RuntimeError("Audio capture already active")

        _active = True
        _output_path = None
        _mode = "dummy"

        if save_audio:
            meeting_dir = paths.meeting_dir(meeting_id)
            meeting_dir.mkdir(parents=True, exist_ok=True)
            _output_path = meeting_dir / "audio.wav"

        force_fake = os.getenv("GIJIROKU21_FAKE_AUDIO", "0") == "1"
        if not force_fake:
            try:
                _start_sounddevice(_output_path)
                _mode = "sounddevice"
            except Exception:
                _mode = "dummy"


def stop_capture() -> None:
    """録音停止。ダミーの場合は無音WAVを出力。"""
    global _active, _output_path, _mode
    with _lock:
        if not _active:
            raise RuntimeError("Audio capture not active")

        if _mode == "sounddevice":
            _stop_sounddevice()
        elif _output_path:
            _write_silence(_output_path)

        _active = False
        _output_path = None
        _mode = "dummy"
