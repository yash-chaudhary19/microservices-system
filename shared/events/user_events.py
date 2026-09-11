from datetime import datetime, timezone
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, EmailStr


class EventHeader(BaseModel):
    """Standard event metadata header."""
    event_id: UUID = Field(default_factory=uuid4, description="Unique identifier for idempotency")
    event_type: str = Field(..., description="Name of the domain event")
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when event occurred in UTC"
    )
    correlation_id: str | None = Field(default=None, description="Request correlation ID")
    schema_version: str = Field(default="v1", description="Event schema version")


class UserCreatedEventV1(BaseModel):
    """Payload for UserCreated event published to NATS JetStream."""
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = "UserCreated"
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: str | None = None
    schema_version: str = "v1"

    user_id: UUID = Field(..., description="ID of newly registered/created user")
    email: EmailStr = Field(..., description="User's email address")
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
