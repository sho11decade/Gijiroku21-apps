from typing import Literal, Optional

from pydantic import BaseModel, Field

EventType = Literal["partial", "final", "status"]


class TranscriptEvent(BaseModel):
    type: EventType = Field(..., description="Event type: partial|final|status")
    text: Optional[str] = Field(None, description="Recognized text when applicable")
    status: Optional[str] = Field(None, description="Status message when type=status")
