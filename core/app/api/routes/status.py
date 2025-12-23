from datetime import datetime

from fastapi import APIRouter

from core.app.models.response import Envelope, success_response
from core.app.models.status import StatusPayload
from core.app.services import recording_state
from core.app.utils import device

router = APIRouter(prefix="/status", tags=["status"])

_start_time = datetime.utcnow()


@router.get("", response_model=Envelope[StatusPayload])
async def get_status() -> Envelope[StatusPayload]:
    rec_state = recording_state.snapshot()
    if rec_state.active:
        ai_state = "listening"
    else:
        ai_state = "ready"

    uptime = int((datetime.utcnow() - _start_time).total_seconds())
    payload = StatusPayload(
        ai_state=ai_state,
        recording=rec_state.active,
        model="whisper-small",
        device=device.selected_device(),
        uptime_sec=uptime,
    )
    return success_response(payload)
