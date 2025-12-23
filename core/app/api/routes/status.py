from datetime import datetime

from fastapi import APIRouter

from core.app.models.response import Envelope, success_response
from core.app.models.status import StatusPayload

router = APIRouter(prefix="/status", tags=["status"])

_start_time = datetime.utcnow()


@router.get("", response_model=Envelope[StatusPayload])
async def get_status() -> Envelope[StatusPayload]:
    uptime = int((datetime.utcnow() - _start_time).total_seconds())
    payload = StatusPayload(
        ai_state="initializing",
        recording=False,
        model="whisper-small",
        device="auto",
        uptime_sec=uptime,
    )
    return success_response(payload)
