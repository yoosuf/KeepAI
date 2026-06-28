from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.database import get_db
from src.main import app
from src.modules.auth.models import Role, User


@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture(autouse=True)
def override_db(mock_db_session):
    app.dependency_overrides[get_db] = lambda: mock_db_session
    yield
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_register_user_success(client, mock_db_session):
    payload = {"email": "newuser@example.com", "password": "password123", "role": "user"}

    # Mocking DB responses
    # 1. Check existing user -> None
    # 2. Check Role -> Return Role Object

    mock_result_user = MagicMock()
    mock_result_user.scalars.return_value.first.return_value = None

    role_obj = Role(id=1, name="user")
    mock_result_role = MagicMock()
    mock_result_role.scalars.return_value.first.return_value = role_obj

    mock_db_session.execute.side_effect = [mock_result_user, mock_result_role]

    # Mock refresh to populate generated fields and relationships
    async def mock_refresh(instance, attribute_names=None):
        instance.id = 1
        instance.is_active = True
        instance.role = role_obj  # Populate relationship for Pydantic response
        return None

    mock_db_session.refresh.side_effect = mock_refresh

    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["is_active"] is True

    # Verify DB interactions
    assert mock_db_session.add.called
    assert mock_db_session.commit.called


@pytest.mark.asyncio
async def test_login_success(client, mock_db_session):
    # Mock User
    argon2_hash = "$argon2id$v=19$m=65536,t=3,p=4$SmCIiixYVIBABP7DSD8czw$BRw+VvIPraEbmAKydRTGSbPJ5/cm4p1YBuTymM9McDo"
    user_obj = User(
        id=1,
        email="test@example.com",
        hashed_password=argon2_hash,  # "secret"
        is_active=True,
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = user_obj
    mock_db_session.execute.return_value = mock_result

    # The hash above is an Argon2id hash of "secret" — uses the real verify_password utility.

    schema = {"username": "test@example.com", "password": "secret"}

    response = await client.post("/api/v1/auth/login", data=schema)  # OAuth2 uses form data

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
