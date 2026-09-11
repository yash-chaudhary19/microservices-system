from typing import Generic, TypeVar, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class ServiceError(BaseModel):
    """Standardized service error payload returned across NATS RPC."""
    code: str = Field(..., description="Machine-readable error code (e.g. USER_NOT_FOUND, INVALID_CREDENTIALS)")
    message: str = Field(..., description="Human-readable error explanation")
    details: dict[str, Any] | list[Any] | None = Field(default=None, description="Optional extra error details")


class ServiceResponse(BaseModel, Generic[T]):
    """Generic wrapper for internal RPC responses across NATS."""
    success: bool
    data: T | None = None
    error: ServiceError | None = None

    @classmethod
    def ok(cls, data: T) -> "ServiceResponse[T]":
        return cls(success=True, data=data, error=None)

    @classmethod
    def fail(cls, code: str, message: str, details: Any = None) -> "ServiceResponse[T]":
        return cls(success=False, data=None, error=ServiceError(code=code, message=message, details=details))
