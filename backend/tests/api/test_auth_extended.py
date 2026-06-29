from unittest.mock import MagicMock

import pytest

from src.modules.auth.models import Role


@pytest.mark.asyncio
async def test_register_duplicate_email(client, override_db, mock_db_session):
    existing_user = MagicMock()
    existing_user.id = 1
    existing_user.email = "existing@test.com"

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = existing_user
    mock_db_session.execute.return_value = mock_result

    payload = {"email": "existing@test.com", "password": "Secure1pass", "role": "user"}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_invalid_role(client, override_db, mock_db_session):
    mock_empty_result = MagicMock()
    mock_empty_result.scalars.return_value.first.return_value = None

    mock_role_result = MagicMock()
    mock_role_result.scalars.return_value.first.return_value = None

    mock_db_session.execute.side_effect = [mock_empty_result, mock_role_result]

    payload = {"email": "new@test.com", "password": "Secure1pass", "role": "nonexistent"}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "Role" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_weak_password(client, override_db, mock_db_session):
    payload = {"email": "new@test.com", "password": "short", "role": "user"}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    assert "8 characters" in response.json()["detail"][0]["msg"]


@pytest.mark.asyncio
async def test_register_password_no_uppercase(client, override_db, mock_db_session):
    payload = {"email": "new@test.com", "password": "lowercase1", "role": "user"}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    assert "uppercase" in response.json()["detail"][0]["msg"]


@pytest.mark.asyncio
async def test_register_password_no_digit(client, override_db, mock_db_session):
    payload = {"email": "new@test.com", "password": "Lowercases", "role": "user"}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    assert "digit" in response.json()["detail"][0]["msg"]


@pytest.mark.asyncio
async def test_login_inactive_user(client, override_db, mock_db_session):
    from src.modules.auth.models import User

    inactive = User(
        id=1,
        email="inactive@test.com",
        hashed_password="not_checked_due_to_is_active",
        is_active=False,
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = inactive
    mock_db_session.execute.return_value = mock_result

    response = await client.post("/api/v1/auth/login", data={"username": "inactive@test.com", "password": "anything"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_wrong_password(client, override_db, mock_db_session):
    from src.modules.auth.models import User

    argon2_hash = "$argon2id$v=19$m=65536,t=3,p=4$tugglF5Fv1Q56USI8+uprQ$dQYj+SjxaH740oxgGyYZhTTMWVI1PWiMuoZEHLqZYe8"
    user = User(id=1, email="user@test.com", hashed_password=argon2_hash, is_active=True)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = user
    mock_db_session.execute.return_value = mock_result

    response = await client.post("/api/v1/auth/login", data={"username": "user@test.com", "password": "wrong"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_success_with_strong_password(client, override_db, mock_db_session):
    mock_empty_result = MagicMock()
    mock_empty_result.scalars.return_value.first.return_value = None

    role_obj = Role(id=2, name="user")
    mock_role_result = MagicMock()
    mock_role_result.scalars.return_value.first.return_value = role_obj

    mock_db_session.execute.side_effect = [mock_empty_result, mock_role_result]

    async def mock_refresh(instance, attribute_names=None):
        instance.id = 1
        instance.is_active = True
        instance.role = role_obj

    mock_db_session.refresh.side_effect = mock_refresh

    payload = {"email": "new@test.com", "password": "Strong1pass", "role": "user"}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    assert response.json()["email"] == "new@test.com"


@pytest.mark.asyncio
async def test_unauthenticated_access(client):
    response = await client.get("/api/v1/prompts")
    assert response.status_code == 401
