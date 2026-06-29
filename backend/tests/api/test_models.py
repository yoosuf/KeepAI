from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


@pytest.mark.asyncio
async def test_list_models(client, override_auth):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"models": [{"name": "llama3:latest", "size": 12345}]}
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        response = await client.get("/api/v1/models")
        assert response.status_code == 200
        data = response.json()
        assert len(data["models"]) == 1
        assert data["models"][0]["name"] == "llama3:latest"


@pytest.mark.asyncio
async def test_list_models_unauthorized(client):
    response = await client.get("/api/v1/models")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_models_ollama_down(client, override_auth):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPError("Connection refused")

    mock_client = MagicMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        response = await client.get("/api/v1/models")
        assert response.status_code == 502
