import uuid
import pytest

pytestmark = pytest.mark.asyncio


async def test_get_user_with_valid_jwt(client, auth_headers, mock_nats_dispatcher):
    user_id = str(uuid.uuid4())
    mock_nats_dispatcher.call.return_value = {
        "id": user_id,
        "name": "Alice Wonderland",
        "email": "alice@example.com",
        "created_at": "2026-09-11T00:00:00Z",
        "updated_at": "2026-09-11T00:00:00Z",
    }

    response = await client.get(f"/users/{user_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == "alice@example.com"


async def test_get_user_unauthorized(client):
    user_id = str(uuid.uuid4())
    response = await client.get(f"/users/{user_id}")

    assert response.status_code == 401
    assert "Not authenticated" in response.text or "detail" in response.json()


async def test_get_user_invalid_token(client):
    user_id = str(uuid.uuid4())
    response = await client.get(
        f"/users/{user_id}",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )

    assert response.status_code == 401


async def test_create_user_with_valid_jwt(client, auth_headers, mock_nats_dispatcher):
    user_id = str(uuid.uuid4())
    mock_nats_dispatcher.call.return_value = {
        "id": user_id,
        "name": "Bob Marley",
        "email": "bob@example.com",
        "created_at": "2026-09-11T00:00:00Z",
        "updated_at": "2026-09-11T00:00:00Z",
    }

    response = await client.post(
        "/users",
        headers=auth_headers,
        json={
            "name": "Bob Marley",
            "email": "bob@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == "bob@example.com"
