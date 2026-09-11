import uuid
from datetime import datetime, timezone
import pytest
from unittest.mock import AsyncMock, patch
from app.services.user_service import UserService
from app.core.security import hash_password
from shared.schemas.user import UserCreateRPCRequest
from app.models.user import User

pytestmark = pytest.mark.asyncio


async def test_create_user_success(mock_session, mock_event_publisher):
    service = UserService(mock_session, mock_event_publisher)

    # Mock repository behavior
    created_user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_created_user = User(
        id=created_user_id,
        name="Bob Builder",
        email="bob@example.com",
        password_hash="hashed_pw",
        created_at=now,
        updated_at=now,
    )

    with patch.object(service.repo, "get_by_email", new_callable=AsyncMock) as mock_get_by_email, \
         patch.object(service.repo, "create", new_callable=AsyncMock) as mock_repo_create:

        mock_get_by_email.return_value = None
        mock_repo_create.return_value = mock_created_user

        req = UserCreateRPCRequest(
            name="Bob Builder",
            email="bob@example.com",
            password="SecurePassword123",
            correlation_id="corr-test-123",
        )

        response = await service.create_user(req)

        assert response.success is True
        assert response.data is not None
        assert response.data.email == "bob@example.com"
        assert response.data.name == "Bob Builder"
        assert response.data.id == created_user_id

        # Verify event was published
        assert mock_event_publisher.publish_user_created.call_count == 1
        published_event = mock_event_publisher.publish_user_created.call_args[0][0]
        assert published_event.user_id == created_user_id
        assert published_event.email == "bob@example.com"
        assert published_event.correlation_id == "corr-test-123"


async def test_create_user_duplicate_email(mock_session, mock_event_publisher, sample_user):
    service = UserService(mock_session, mock_event_publisher)

    with patch.object(service.repo, "get_by_email", new_callable=AsyncMock) as mock_get_by_email:
        mock_get_by_email.return_value = sample_user

        req = UserCreateRPCRequest(
            name="Duplicate Alice",
            email="alice@example.com",
            password="SecurePassword123",
        )

        response = await service.create_user(req)

        assert response.success is False
        assert response.error is not None
        assert response.error.code == "EMAIL_ALREADY_EXISTS"
        # Ensure event was not published
        assert mock_event_publisher.publish_user_created.call_count == 0


async def test_get_user_success(mock_session, sample_user):
    service = UserService(mock_session)

    with patch.object(service.repo, "get_by_id", new_callable=AsyncMock) as mock_get_by_id:
        mock_get_by_id.return_value = sample_user

        response = await service.get_user(sample_user.id)

        assert response.success is True
        assert response.data is not None
        assert response.data.id == sample_user.id
        assert response.data.email == sample_user.email


async def test_get_user_not_found(mock_session):
    service = UserService(mock_session)

    with patch.object(service.repo, "get_by_id", new_callable=AsyncMock) as mock_get_by_id:
        mock_get_by_id.return_value = None

        unknown_id = uuid.uuid4()
        response = await service.get_user(unknown_id)

        assert response.success is False
        assert response.error is not None
        assert response.error.code == "USER_NOT_FOUND"


async def test_authenticate_user_success(mock_session):
    service = UserService(mock_session)
    password = "CorrectPassword123"
    hashed = hash_password(password)
    now = datetime.now(timezone.utc)

    user = User(
        id=uuid.uuid4(),
        name="Charlie",
        email="charlie@example.com",
        password_hash=hashed,
        created_at=now,
        updated_at=now,
    )

    with patch.object(service.repo, "get_by_email", new_callable=AsyncMock) as mock_get_by_email:
        mock_get_by_email.return_value = user

        response = await service.authenticate_user("charlie@example.com", password)

        assert response.success is True
        assert response.data is not None
        assert response.data.id == user.id
        assert response.data.email == user.email


async def test_authenticate_user_invalid_password(mock_session):
    service = UserService(mock_session)
    hashed = hash_password("CorrectPassword123")
    now = datetime.now(timezone.utc)

    user = User(
        id=uuid.uuid4(),
        name="Charlie",
        email="charlie@example.com",
        password_hash=hashed,
        created_at=now,
        updated_at=now,
    )

    with patch.object(service.repo, "get_by_email", new_callable=AsyncMock) as mock_get_by_email:
        mock_get_by_email.return_value = user

        response = await service.authenticate_user("charlie@example.com", "WrongPassword")

        assert response.success is False
        assert response.error is not None
        assert response.error.code == "INVALID_CREDENTIALS"
