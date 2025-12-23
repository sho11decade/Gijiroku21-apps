from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    language: str = Field(default="ja", description="Default language code for ASR")
    model: str = Field(default="small", description="Model size identifier")
    save_audio: bool = Field(default=True, description="Whether to persist raw audio files")
