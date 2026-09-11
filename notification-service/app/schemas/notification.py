from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class NotificationCreateInternal(BaseModel):
    user_id: UUID
    type: str = "WELCOME_EMAIL"
    title: str = Field(..., max_length=150)
    message: str
    status: str = "created"
    event_id: UUID


class NotificationResponseInternal(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    title: str
    message: str
    status: str
    event_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
