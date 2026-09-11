import uuid
import pytest

pytestmark = pytest.mark.asyncio


async def test_get_notifications_with_valid_jwt(client, auth_headers, mock_nats_dispatcher):
    user_id = str(uuid.uuid4())
    event_id = str(uuid.uuid4())
    notif_id = str(uuid.uuid4())

    mock_nats_dispatcher.call.return_value = {
        "notifications": [
            {
                "id": notif_id,
                "user_id": user_id,
                "type": "WELCOME_EMAIL",
                "title": "Welcome!",
                "message": "Welcome to the platform, Alice.",
                "status": "created",
                "event_id": event_id,
                "created_at": "2026-09-11T00:00:00Z",
            }
        ],
        "total": 1,
    }

    response = await client.get(f"/notifications/{user_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["notifications"]) == 1
    assert data["notifications"][0]["id"] == notif_id
    assert data["notifications"][0]["event_id"] == event_id


async def test_get_notifications_unauthorized(client):
    user_id = str(uuid.uuid4())
    response = await client.get(f"/notifications/{user_id}")

    assert response.status_code == 401
