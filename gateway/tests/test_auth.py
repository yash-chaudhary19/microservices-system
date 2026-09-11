import uuid
import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock

pytestmark = pytest.mark.asyncio


async def test_register_success(client, mock_nats_dispatcher):
    user_id = str(uuid.uuid4())
    mock_nats_dispatcher.call.return_value = {
        "id": user_id,
        "name": "Jane Doe",
        "email": "jane@example.com",
        "created_at": "2026-09-11T00:00:00Z",
        "updated_at": "2026-09-11T00:00:00Z",
    }

    response = await client.post(
        "/auth/register",
        json={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "jane@example.com"
    assert data["user"]["id"] == user_id


async def test_register_weak_password(client):
    response = await client.post(
        "/auth/register",
        json={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "simple",  # too short and no numbers
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


async def test_register_duplicate_email(client, mock_nats_dispatcher):
    mock_nats_dispatcher.call.side_effect = HTTPException(
        status_code=409,
        detail={"code": "EMAIL_ALREADY_EXISTS", "message": "Email already exists."},
    )

    response = await client.post(
        "/auth/register",
        json={
            "name": "Jane Doe",
            "email": "existing@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 409


async def test_login_success(client, mock_nats_dispatcher):
    user_id = str(uuid.uuid4())
    mock_nats_dispatcher.call.return_value = {
        "id": user_id,
        "name": "Jane Doe",
        "email": "jane@example.com",
    }

    response = await client.post(
        "/auth/login",
        json={
            "email": "jane@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["id"] == user_id


async def test_login_invalid_credentials(client, mock_nats_dispatcher):
    mock_nats_dispatcher.call.side_effect = HTTPException(
        status_code=401,
        detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password."},
    )

    response = await client.post(
        "/auth/login",
        json={
            "email": "jane@example.com",
            "password": "WrongPassword",
        },
    )

    assert response.status_code == 401
