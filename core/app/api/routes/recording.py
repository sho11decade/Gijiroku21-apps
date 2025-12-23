from datetime import datetime

from fastapi import APIRouter, HTTPException

from core.app.models.recording import (
    StartRecordingRequest,
    StartRecordingResponse,
    StopRecordingResponse,
)
from core.app.models.response import Envelope, success_response
from core.app.services import recording_state
from core.app.utils import paths

router = APIRouter(prefix="/record", tags=["record"])


@router.post("/start", response_model=Envelope[StartRecordingResponse])
async def start_recording(payload: StartRecordingRequest) -> Envelope[StartRecordingResponse]:
    now = datetime.utcnow()
    meeting_id = now.strftime("%Y-%m-%d-%H%M%S")

    try:
        recording_state.start(meeting_id)
    except RuntimeError as exc:  # already active
        raise HTTPException(status_code=400, detail=str(exc))

    # Ensure storage directories exist up-front
    paths.ensure_base_dirs()
    meeting_dir = paths.meeting_dir(meeting_id)
    meeting_dir.mkdir(parents=True, exist_ok=True)

    return success_response(StartRecordingResponse(meeting_id=meeting_id))


@router.post("/stop", response_model=Envelope[StopRecordingResponse])
async def stop_recording() -> Envelope[StopRecordingResponse]:
    try:
        _ = recording_state.stop()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # TODO: calculate real duration once audio pipeline is connected
    return success_response(StopRecordingResponse(duration_sec=0))
