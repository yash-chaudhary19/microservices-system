import uuid
from datetime import datetime, timezone
import pytest
from unittest.mock import AsyncMock, patch
from app.services.notification_service import NotificationService
from shared.events.user_events import UserCreatedEventV1
from app.models.notification import Notification

pytestmark = pytest.mark.asyncio


async def test_process_user_created_event_new(mock_session):
    service = NotificationService(mock_session)

    user_id = uuid.uuid4()
    event_id = uuid.uuid4()
    event = UserCreatedEventV1(
        event_id=event_id,
        user_id=user_id,
        email="newuser@example.com",
        name="New User",
    )

    created_notification = Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        event_id=event_id,
        title="Welcome!",
        message="Welcome to the platform, New User.",
        type="WELCOME_EMAIL",
        status="created",
        created_at=datetime.now(timezone.utc),
    )

    with patch.object(service.repo, "get_by_event_id", new_callable=AsyncMock) as mock_get_by_event_id, \
         patch.object(service.repo, "create", new_callable=AsyncMock) as mock_create:

        mock_get_by_event_id.return_value = None
        mock_create.return_value = created_notification

        result = await service.process_user_created_event(event)

        assert result.id == created_notification.id
        assert result.user_id == user_id
        assert result.event_id == event_id
        assert result.title == "Welcome!"
        assert "New User" in result.message

        assert mock_create.call_count == 1


async def test_process_user_created_event_idempotency(mock_session, sample_notification):
    """Verifies that an event with identical event_id is safely ignored and not duplicated."""
    service = NotificationService(mock_session)

    event = UserCreatedEventV1(
        event_id=sample_notification.event_id,
        user_id=sample_notification.user_id,
        email="alice@example.com",
        name="Alice",
    )

    with patch.object(service.repo, "get_by_event_id", new_callable=AsyncMock) as mock_get_by_event_id, \
         patch.object(service.repo, "create", new_callable=AsyncMock) as mock_create:

        mock_get_by_event_id.return_value = sample_notification

        result = await service.process_user_created_event(event)

        assert result.id == sample_notification.id
        assert result.event_id == sample_notification.event_id
        # Crucial check: repo.create MUST NOT be called again
        assert mock_create.call_count == 0


async def test_get_user_notifications(mock_session, sample_notification):
    service = NotificationService(mock_session)

    with patch.object(service.repo, "get_by_user_id", new_callable=AsyncMock) as mock_get_by_user_id:
        mock_get_by_user_id.return_value = [sample_notification]

        response = await service.get_user_notifications(sample_notification.user_id)

        assert response.success is True
        assert response.data is not None
        assert response.data.total == 1
        assert response.data.notifications[0].id == sample_notification.id
