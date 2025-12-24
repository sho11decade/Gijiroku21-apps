from fastapi import APIRouter, HTTPException

from core.app.models.meeting import MeetingDetail, MeetingListItem
from core.app.models.response import Envelope, success_response
from core.app.utils import storage

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.get("", response_model=Envelope[list[MeetingListItem]])
async def list_meetings() -> Envelope[list[MeetingListItem]]:
    items = storage.list_meetings()
    return success_response(items)


@router.get("/{meeting_id}", response_model=Envelope[MeetingDetail])
async def get_meeting(meeting_id: str) -> Envelope[MeetingDetail]:
    detail = storage.load_detail(meeting_id)
    if not detail:
        raise HTTPException(status_code=404, detail="meeting not found")
    return success_response(detail)
