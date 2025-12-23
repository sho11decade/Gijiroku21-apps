from pydantic import BaseModel, Field


class StatusPayload(BaseModel):
    ai_state: str = Field(..., description="Core state: initializing|ready|listening|processing|error")
    recording: bool = Field(..., description="Whether recording is active")
    model: str = Field(..., description="Model identifier")
    device: str = Field(..., description="Selected device: NPU|CPU|GPU|auto")
    uptime_sec: int = Field(..., description="Seconds since process start")
