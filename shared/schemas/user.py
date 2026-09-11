from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreateRPCRequest(BaseModel):
    """Payload sent via NATS to create a user."""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    correlation_id: str | None = None


class UserGetRPCRequest(BaseModel):
    """Payload sent via NATS to retrieve a user."""
    user_id: UUID
    correlation_id: str | None = None


class UserAuthenticateRPCRequest(BaseModel):
    """Payload sent via NATS to authenticate user credentials."""
    email: EmailStr
    password: str
    correlation_id: str | None = None


class UserDTO(BaseModel):
    """User representation without password hash."""
    id: UUID
    name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserAuthResultDTO(BaseModel):
    """User representation returned after successful credential verification."""
    id: UUID
    name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)
