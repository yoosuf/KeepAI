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
async def test_create_prompt_success(prompt_service, mock_llm_client, mock_db):
    # Setup
    user_id = 1
    prompt_text = "test prompt"
    expected_response = "test response"

    mock_llm_client.generate.return_value = {
        "response_text": expected_response,
        "processing_time_ms": 100,
        "meta_data": {},
    }

    # Execute
    result = await prompt_service.create_prompt(prompt_text, user_id)

    # Verify
    assert isinstance(result, Prompt)
    assert result.prompt_text == prompt_text
    assert result.response_text == expected_response
    assert result.user_id == user_id

    # Verify DB interactions
    mock_db.section.add.assert_not_called()  # AsyncMock structure varies, but we check calls
    assert mock_db.add.called
    assert mock_db.commit.called
    assert mock_db.refresh.called


@pytest.mark.asyncio
async def test_create_prompt_llm_failure(prompt_service, mock_llm_client):
    # Setup
    mock_llm_client.generate.side_effect = Exception("LLM Error")

    # Execute & Verify
    with pytest.raises(Exception) as exc:
        await prompt_service.create_prompt("test", 1)
    assert "LLM Error" in str(exc.value)
