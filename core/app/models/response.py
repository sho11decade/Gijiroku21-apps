from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    code: str = Field(..., description="Stable error code without sensitive detail")
    message: str = Field(..., description="Human-readable error message")


class Envelope(BaseModel, Generic[T]):
    success: bool = Field(default=True, description="Indicates whether the request succeeded")
    data: Optional[T] = Field(default=None, description="Response payload when success is true")
    error: Optional[ErrorResponse] = Field(default=None, description="Error information when success is false")


def success_response(data: Optional[T] = None) -> Envelope[T]:
    return Envelope(success=True, data=data, error=None)


def error_response(code: str, message: str) -> Envelope[None]:
    return Envelope(success=False, data=None, error=ErrorResponse(code=code, message=message))
