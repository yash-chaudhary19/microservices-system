import pytest
from unittest.mock import MagicMock
from app.main import app

pytestmark = pytest.mark.asyncio


async def test_gateway_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "api-gateway"


async def test_gateway_readiness_connected(client):
    mock_mgr = MagicMock()
    mock_mgr.nc.is_closed = False
    app.state.nats_manager = mock_mgr

    response = await client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["nats"] == "connected"
