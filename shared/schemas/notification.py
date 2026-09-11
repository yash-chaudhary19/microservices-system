from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class NotificationListRPCRequest(BaseModel):
    """Payload sent via NATS to list notifications for a specific user."""
    user_id: UUID
    correlation_id: str | None = None


class NotificationDTO(BaseModel):
    """Notification representation."""
    id: UUID
    user_id: UUID
    type: str
    title: str
    message: str
    status: str
    event_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListDTO(BaseModel):
    """List of notifications."""
    notifications: list[NotificationDTO]
    total: int
