from dataclasses import dataclass
from threading import Lock
from typing import Optional


@dataclass
class RecordingState:
    active: bool = False
    meeting_id: Optional[str] = None


_state = RecordingState()
_lock = Lock()


def start(meeting_id: str) -> None:
    with _lock:
        if _state.active:
            raise RuntimeError("Recording already in progress")
        _state.active = True
        _state.meeting_id = meeting_id


def stop() -> str:
    with _lock:
        if not _state.active or not _state.meeting_id:
            raise RuntimeError("Recording not active")
        meeting_id = _state.meeting_id
        _state.active = False
        _state.meeting_id = None
        return meeting_id


def snapshot() -> RecordingState:
    with _lock:
        return RecordingState(active=_state.active, meeting_id=_state.meeting_id)
