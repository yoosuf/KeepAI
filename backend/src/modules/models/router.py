import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from src.core.config import settings
from src.modules.auth.models import User
from src.modules.auth.service import PermissionChecker, get_current_user
from src.modules.models.schemas import (
    ModelDeleteResponse,
    ModelListResponse,
    ModelPullRequest,
    ModelPullResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _ollama_url(path: str) -> str:
    return f"{settings.OLLAMA_BASE_URL}{path}"


@router.get("", response_model=ModelListResponse)
async def list_models(current_user: User = Depends(get_current_user)):
    """List all models currently available in Ollama."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(_ollama_url("/api/tags"))
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError as e:
        logger.error(f"Ollama list models error: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to reach Ollama") from e


@router.post("/pull", response_model=ModelPullResponse)
async def pull_model(
    body: ModelPullRequest,
    current_user: User = Depends(PermissionChecker("models:manage")),
):
    """Admin only: Pull a model from the Ollama registry. Blocks until complete."""
    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            # stream=False collects the full NDJSON; we only surface the final status line
            resp = await client.post(
                _ollama_url("/api/pull"),
                json={"name": body.name, "insecure": body.insecure, "stream": False},
            )
            resp.raise_for_status()
            data = resp.json()
            return ModelPullResponse(status=data.get("status", "success"))
    except httpx.HTTPError as e:
        logger.error(f"Ollama pull error: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Pull failed: {e}") from e


@router.delete("/{model_name:path}", response_model=ModelDeleteResponse)
async def delete_model(
    model_name: str,
    current_user: User = Depends(PermissionChecker("models:manage")),
):
    """Admin only: Delete a model from Ollama local storage."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request("DELETE", _ollama_url("/api/delete"), json={"name": model_name})
            resp.raise_for_status()
            return ModelDeleteResponse(status="deleted")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found") from e
        logger.error(f"Ollama delete error: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Delete failed: {e}") from e
    except httpx.HTTPError as e:
        logger.error(f"Ollama delete error: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Delete failed: {e}") from e
