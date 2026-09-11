import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.notification_repository import NotificationRepository
from shared.events.user_events import UserCreatedEventV1
from shared.schemas.notification import (
    NotificationDTO,
    NotificationListDTO,
)
from shared.schemas.common import ServiceResponse

logger = logging.getLogger("notification_service.service")


class NotificationService:
    """Core domain logic for Notification Service."""

    def __init__(self, session: AsyncSession):
        self.repo = NotificationRepository(session)

    async def process_user_created_event(self, event: UserCreatedEventV1) -> NotificationDTO:
        """Process UserCreated event idempotently and create welcome notification."""
        # 1. Check for duplicate event processing (Idempotency)
        existing = await self.repo.get_by_event_id(event.event_id)
        if existing:
            logger.info(
                f"Idempotency hit: Event {event.event_id} has already been processed for user {event.user_id}. Skipping creation."
            )
            return NotificationDTO.model_validate(existing)

        # 2. Build notification content
        title = "Welcome!"
        message = f"Welcome to the platform, {event.name}."

        # 3. Persist notification
        notification = await self.repo.create(
            user_id=event.user_id,
            event_id=event.event_id,
            title=title,
            message=message,
            notification_type="WELCOME_EMAIL",
            status="created",
        )
        logger.info(
            f"Successfully processed UserCreated event {event.event_id}. "
            f"Created notification {notification.id} for user {event.user_id}."
        )
        return NotificationDTO.model_validate(notification)

    async def get_user_notifications(self, user_id: UUID) -> ServiceResponse[NotificationListDTO]:
        """Retrieve notifications for a user."""
        notifications = await self.repo.get_by_user_id(user_id)
        dto_list = [NotificationDTO.model_validate(n) for n in notifications]
        return ServiceResponse.ok(
            NotificationListDTO(
                notifications=dto_list,
                total=len(dto_list),
            )
        )
