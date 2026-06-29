from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.modules.auth.models import User
from src.modules.prompts.models import Prompt


@pytest.mark.asyncio
async def test_admin_list_users(client, override_db, override_auth, mock_db_session):
    user_obj = MagicMock(spec=User)
    user_obj.id = 1
    user_obj.email = "admin@test.com"
    user_obj.is_active = True
    user_obj.role = MagicMock()
    user_obj.role.name = "admin"

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [user_obj]
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/admin/users")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"] == "admin@test.com"


@pytest.mark.asyncio
async def test_admin_list_prompts(client, override_db, override_auth, mock_db_session):
    prompt_obj = MagicMock(spec=Prompt)
    prompt_obj.id = 1
    prompt_obj.prompt_text = "test"
    prompt_obj.response_text = "response"
    prompt_obj.model_name = "llama3"
    prompt_obj.user_id = 1
    prompt_obj.meta_data = {}
    prompt_obj.created_at = datetime.now(timezone.utc)
    prompt_obj.updated_at = datetime.now(timezone.utc)
    prompt_obj.processing_time_ms = 100

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [prompt_obj]
    mock_db_session.execute.return_value = mock_result

    response = await client.get("/api/v1/admin/all-prompts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["prompt_text"] == "test"


@pytest.mark.asyncio
async def test_admin_list_users_forbidden_without_permission(
    client, override_db, override_auth_regular, mock_db_session
):
    response = await client.get("/api/v1/admin/users")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_list_prompts_forbidden_without_permission(
    client, override_db, override_auth_regular, mock_db_session
):
    response = await client.get("/api/v1/admin/all-prompts")
    assert response.status_code == 403
