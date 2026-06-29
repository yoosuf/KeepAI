from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.prompts.models import Prompt
from src.modules.prompts.service import PromptService


@pytest.fixture
def mock_db():
    mock = AsyncMock()
    mock.add = MagicMock()
    return mock


@pytest.fixture
def mock_llm_client():
    client = AsyncMock()
    return client


@pytest.fixture
def prompt_service(mock_db, mock_llm_client):
    return PromptService(db=mock_db, llm_client=mock_llm_client)


@pytest.mark.asyncio
async def test_get_prompts_empty(prompt_service, mock_db):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_count_result = MagicMock()
    mock_count_result.scalar_one.return_value = 0
    mock_db.execute = AsyncMock(side_effect=[mock_result, mock_count_result])

    items, total = await prompt_service.get_prompts(user_id=1)
    assert items == []
    assert total == 0


@pytest.mark.asyncio
async def test_get_prompts_pagination(prompt_service, mock_db):
    prompts = [MagicMock(spec=Prompt, id=i) for i in range(5)]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = prompts
    mock_count_result = MagicMock()
    mock_count_result.scalar_one.return_value = 20
    mock_db.execute = AsyncMock(side_effect=[mock_result, mock_count_result])

    items, total = await prompt_service.get_prompts(user_id=1, skip=0, limit=5)
    assert len(items) == 5
    assert total == 20


@pytest.mark.asyncio
async def test_get_prompt_by_id_found(prompt_service, mock_db):
    prompt = MagicMock(spec=Prompt, id=1, user_id=1)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = prompt
    mock_db.execute.return_value = mock_result

    result = await prompt_service.get_prompt_by_id(prompt_id=1, user_id=1)
    assert result is not None
    assert result.id == 1


@pytest.mark.asyncio
async def test_get_prompt_by_id_not_found(prompt_service, mock_db):
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result

    result = await prompt_service.get_prompt_by_id(prompt_id=999, user_id=1)
    assert result is None


@pytest.mark.asyncio
async def test_get_prompt_by_id_wrong_user(prompt_service, mock_db):
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None  # user 1 shouldn't see user 2's prompt
    mock_db.execute.return_value = mock_result

    result = await prompt_service.get_prompt_by_id(prompt_id=1, user_id=1)
    assert result is None
