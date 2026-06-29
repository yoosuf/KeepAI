import os
from unittest.mock import AsyncMock, MagicMock

# Set dummy env vars for testing before importing app/config
os.environ["POSTGRES_USER"] = "test_user"
os.environ["POSTGRES_PASSWORD"] = "test_password"
os.environ["POSTGRES_SERVER"] = "localhost"
os.environ["POSTGRES_DB"] = "test_db"
os.environ["SECRET_KEY"] = "test_secret"


import pytest
from httpx import ASGITransport, AsyncClient

from src.core.database import get_db
from src.main import app
from src.modules.auth.models import Permission, Role, User
from src.modules.auth.service import get_current_user, get_current_user_with_permissions

# Provide a mock LLM client so endpoints that depend on get_prompt_service work
app.state.llm_client = AsyncMock()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    yield
    app.dependency_overrides = {}


@pytest.fixture
def override_db(mock_db_session):
    app.dependency_overrides[get_db] = lambda: mock_db_session
    yield


_admin_perms = [
    Permission(id=1, name="users:read"),
    Permission(id=2, name="prompts:read_all"),
    Permission(id=3, name="prompts:create"),
    Permission(id=4, name="models:manage"),
]
_user_perms = [Permission(id=3, name="prompts:create")]
_admin_role = Role(id=1, name="admin", permissions=_admin_perms)
_user_role = Role(id=2, name="user", permissions=_user_perms)


@pytest.fixture
def admin_user():
    return User(id=1, email="admin@test.com", hashed_password="...", is_active=True, role=_admin_role)


@pytest.fixture
def regular_user():
    return User(id=2, email="user@test.com", hashed_password="...", is_active=True, role=_user_role)


@pytest.fixture
def inactive_user():
    return User(id=3, email="inactive@test.com", hashed_password="...", is_active=False, role=_user_role)


@pytest.fixture
def override_auth(admin_user):
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_current_user_with_permissions] = lambda: admin_user
    yield


@pytest.fixture
def override_auth_regular(regular_user):
    app.dependency_overrides[get_current_user] = lambda: regular_user
    app.dependency_overrides[get_current_user_with_permissions] = lambda: regular_user
    yield
