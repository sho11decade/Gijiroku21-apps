from datetime import datetime

from fastapi import APIRouter, HTTPException

from core.app.models.recording import (
    StartRecordingRequest,
    StartRecordingResponse,
    StopRecordingResponse,
)
from core.app.models.response import Envelope, success_response
from core.app.models.meeting import MeetingMeta
from core.app.services import asr_pipeline, audio_capture
from core.app.services import recording_state
from core.app.utils import paths, storage

router = APIRouter(prefix="/record", tags=["record"])


@router.post("/start", response_model=Envelope[StartRecordingResponse])
async def start_recording(payload: StartRecordingRequest) -> Envelope[StartRecordingResponse]:
    now = datetime.utcnow()
    meeting_id = now.strftime("%Y-%m-%d-%H%M%S")

    try:
        recording_state.start(meeting_id)
    except RuntimeError as exc:  # already active
        raise HTTPException(status_code=400, detail=str(exc))

    # Hook for audio capture start
    audio_capture.start_capture(meeting_id=meeting_id, save_audio=payload.save_audio)

    # Start dummy ASR pipeline (replace with real pipeline later)
    try:
        await asr_pipeline.start(meeting_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Write initial meta
    meta = MeetingMeta(
        meeting_id=meeting_id,
        title=payload.meeting_title,
        started_at=now,
        audio_path=str(paths.meeting_dir(meeting_id) / "audio.wav") if payload.save_audio else None,
        transcript_path=str(paths.transcript_file(meeting_id)),
        summary_path=str(paths.summary_file(meeting_id)),
    )
    storage.save_meta(meta)

    # Ensure storage directories exist up-front
    paths.ensure_base_dirs()
    meeting_dir = paths.meeting_dir(meeting_id)
    meeting_dir.mkdir(parents=True, exist_ok=True)

    return success_response(StartRecordingResponse(meeting_id=meeting_id))


@router.post("/stop", response_model=Envelope[StopRecordingResponse])
async def stop_recording() -> Envelope[StopRecordingResponse]:
    try:
        meeting_id, started_at = recording_state.stop()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Hook for audio capture stop
    audio_capture.stop_capture()

    # Stop ASR pipeline
    await asr_pipeline.stop()

    duration = 0
    ended_at = datetime.utcnow()
    if started_at:
        duration = int((ended_at - started_at).total_seconds())

    existing_meta = storage.load_meta(meeting_id)
    if existing_meta:
        existing_meta.ended_at = ended_at
        existing_meta.duration_sec = duration
        storage.save_meta(existing_meta)

    return success_response(StopRecordingResponse(duration_sec=duration))
