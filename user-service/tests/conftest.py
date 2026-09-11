import uuid
from datetime import datetime, timezone
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.models.user import User
from app.messaging.event_publisher import EventPublisher


@pytest.fixture
def mock_session():
    """Mock SQLAlchemy AsyncSession."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_event_publisher():
    """Mock JetStream EventPublisher."""
    publisher = AsyncMock(spec=EventPublisher)
    publisher.publish_user_created = AsyncMock()
    publisher.ensure_stream_exists = AsyncMock()
    return publisher


@pytest.fixture
def sample_user():
    """Sample User model instance."""
    now = datetime.now(timezone.utc)
    return User(
        id=uuid.uuid4(),
        name="Alice Johnson",
        email="alice@example.com",
        password_hash="$2b$12$e8Y6qB2m0J3aT.dummyhash",
        created_at=now,
        updated_at=now,
    )
