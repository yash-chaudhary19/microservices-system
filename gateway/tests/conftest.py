import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock
from app.main import app
from app.clients.nats_client import GatewayNATSDispatcher
from app.core.security import create_access_token


@pytest.fixture
def mock_nats_dispatcher():
    """Mock GatewayNATSDispatcher."""
    dispatcher = AsyncMock(spec=GatewayNATSDispatcher)
    dispatcher.call = AsyncMock()
    return dispatcher


@pytest.fixture
async def client(mock_nats_dispatcher):
    """Async test client with mocked NATS dispatcher attached to app state."""
    app.state.nats_dispatcher = mock_nats_dispatcher
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def valid_jwt_token():
    """Generates a valid JWT token for test user."""
    user_id = uuid.uuid4()
    email = "testuser@example.com"
    token = create_access_token(user_id=user_id, email=email)
    return token, user_id, email


@pytest.fixture
def auth_headers(valid_jwt_token):
    token, _, _ = valid_jwt_token
    return {"Authorization": f"Bearer {token}"}
