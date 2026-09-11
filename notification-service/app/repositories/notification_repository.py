from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.notification import Notification


class NotificationRepository:
    """Repository handling Notification persistence and querying."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_event_id(self, event_id: UUID) -> Notification | None:
        """Fetch notification by source event_id (idempotency check)."""
        stmt = select(Notification).where(Notification.event_id == event_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID) -> list[Notification]:
        """Fetch all notifications for a specific user ordered by newest first."""
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        user_id: UUID,
        event_id: UUID,
        title: str,
        message: str,
        notification_type: str = "WELCOME_EMAIL",
        status: str = "created",
    ) -> Notification:
        """Create and persist a new notification."""
        notification = Notification(
            user_id=user_id,
            event_id=event_id,
            title=title,
            message=message,
            type=notification_type,
            status=status,
        )
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification
