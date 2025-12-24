from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MeetingMeta(BaseModel):
    meeting_id: str = Field(..., description="Unique meeting identifier")
    title: str = Field(..., description="Meeting title")
    started_at: datetime = Field(..., description="UTC timestamp when recording started")
    ended_at: Optional[datetime] = Field(None, description="UTC timestamp when recording stopped")
    duration_sec: Optional[int] = Field(None, description="Duration in seconds")
    transcript_path: Optional[str] = Field(None, description="Path to transcript file if exists")
    summary_path: Optional[str] = Field(None, description="Path to summary file if exists")
    audio_path: Optional[str] = Field(None, description="Path to audio.wav if saved")


class MeetingListItem(BaseModel):
    meeting_id: str
    title: str
    date: str
    duration_sec: Optional[int] = None


class MeetingDetail(BaseModel):
    meta: MeetingMeta
    transcript: Optional[str] = None
    summary: Optional[str] = None
