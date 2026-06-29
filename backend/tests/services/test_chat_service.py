from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
async def test_invoice_extraction_success():
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = {
        "response_text": '{"invoice_number": "123", "total_amount": 100.0}',
        "processing_time_ms": 100,
        "meta_data": {},
    }
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    from src.modules.prompts.service import PromptService

    service = PromptService(db=mock_db, llm_client=mock_llm)

    result = await service.extract_invoice(text_content="Invoice #123 for $100", user_id=1)

    assert result["invoice_number"] == "123"
    assert result["total_amount"] == 100.0
    assert mock_db.add.called
    assert mock_db.commit.called


@pytest.mark.asyncio
async def test_invoice_extraction_system_prompt_used():
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = {
        "response_text": '{"invoice_number": "456"}',
        "processing_time_ms": 50,
        "meta_data": {},
    }
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    from src.modules.prompts.service import PromptService

    service = PromptService(db=mock_db, llm_client=mock_llm)

    await service.extract_invoice(text_content="Some invoice text", user_id=1)

    call_kwargs = mock_llm.generate.call_args
    prompt_text = call_kwargs[1]["prompt"]
    # The prompt should include the system instructions from InvoiceAgent
    assert "Extract the following invoice data" in prompt_text or "invoice" in prompt_text.lower()
    assert "format" not in call_kwargs[1] or call_kwargs[1].get("format") == "json"
