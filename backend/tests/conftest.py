import os

# Set dummy env vars for testing before importing app/config
os.environ["POSTGRES_USER"] = "test_user"
os.environ["POSTGRES_PASSWORD"] = "test_password"
os.environ["POSTGRES_SERVER"] = "localhost"
os.environ["POSTGRES_DB"] = "test_db"
os.environ["SECRET_KEY"] = "test_secret"

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
