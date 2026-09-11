import uuid
from datetime import datetime, timezone
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.models.notification import Notification


@pytest.fixture
def mock_session():
    """Mock SQLAlchemy AsyncSession for notification tests."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def sample_notification():
    """Sample Notification model instance."""
    return Notification(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        event_id=uuid.uuid4(),
        title="Welcome!",
        message="Welcome to the platform, Alice.",
        type="WELCOME_EMAIL",
        status="created",
        created_at=datetime.now(timezone.utc),
    )
