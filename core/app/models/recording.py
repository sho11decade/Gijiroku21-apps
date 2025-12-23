from pydantic import BaseModel, Field


class StartRecordingRequest(BaseModel):
    meeting_title: str = Field(..., description="Human-readable meeting title")
    language: str = Field(default="ja", description="Language code; defaults to Japanese")
    save_audio: bool = Field(default=True, description="Whether to persist audio.wav")


class StartRecordingResponse(BaseModel):
    meeting_id: str = Field(..., description="Unique meeting identifier")


class StopRecordingResponse(BaseModel):
    duration_sec: int = Field(..., description="Elapsed seconds for the meeting recording")
