from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.core.rate_limit import limiter
from src.modules.auth.models import User
from src.modules.auth.service import get_current_user
from src.modules.prompts.schemas import InvoiceExtractRequest, PaginatedPromptResponse, PromptCreate, PromptResponse
from src.modules.prompts.service import PromptService

router = APIRouter()


def get_prompt_service(request: Request, db: AsyncSession = Depends(get_db)) -> PromptService:
    return PromptService(db, request.app.state.llm_client)


@router.post("/prompts", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_LLM)
async def create_prompt(
    request: Request,
    prompt_in: PromptCreate,
    service: PromptService = Depends(get_prompt_service),
    current_user: User = Depends(get_current_user),
):
    resolved_model = (
        prompt_in.model_name
        or (prompt_in.task_type and settings.MODEL_ROUTING.get(prompt_in.task_type))
        or settings.OLLAMA_MODEL
    )
    try:
        return await service.create_prompt(
            prompt_text=prompt_in.prompt_text,
            user_id=current_user.id,
            model=resolved_model,
            system_prompt=prompt_in.system_prompt,
            temperature=prompt_in.temperature,
            top_p=prompt_in.top_p,
            max_tokens=prompt_in.max_tokens,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process prompt: {e}",
        ) from e


@router.post("/prompts/stream", status_code=status.HTTP_200_OK)
@limiter.limit(settings.RATE_LIMIT_LLM)
async def stream_prompt(
    request: Request,
    prompt_in: PromptCreate,
    service: PromptService = Depends(get_prompt_service),
    current_user: User = Depends(get_current_user),
):
    """Stream LLM tokens via Server-Sent Events. Not persisted to DB."""

    resolved_model = (
        prompt_in.model_name
        or (prompt_in.task_type and settings.MODEL_ROUTING.get(prompt_in.task_type))
        or settings.OLLAMA_MODEL
    )
    stream_kwargs: dict = {}
    if prompt_in.system_prompt:
        stream_kwargs["system"] = prompt_in.system_prompt
    if prompt_in.temperature is not None:
        stream_kwargs["temperature"] = prompt_in.temperature
    if prompt_in.top_p is not None:
        stream_kwargs["top_p"] = prompt_in.top_p
    if prompt_in.max_tokens is not None:
        stream_kwargs["num_predict"] = prompt_in.max_tokens

    async def _event_generator() -> AsyncGenerator[str, None]:
        try:
            async for token in service.llm_client.stream_generate(
                prompt=prompt_in.prompt_text,
                model=resolved_model,
                **stream_kwargs,
            ):
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: [ERROR] {e}\n\n"

    return StreamingResponse(_event_generator(), media_type="text/event-stream")


@router.get("/prompts", response_model=PaginatedPromptResponse)
async def get_prompts(
    skip: int = 0,
    limit: int = 20,
    service: PromptService = Depends(get_prompt_service),
    current_user: User = Depends(get_current_user),
):
    items, total = await service.get_prompts(user_id=current_user.id, skip=skip, limit=limit)
    return PaginatedPromptResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/prompts/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: int,
    service: PromptService = Depends(get_prompt_service),
    current_user: User = Depends(get_current_user),
):
    prompt = await service.get_prompt_by_id(prompt_id, user_id=current_user.id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.post("/extract-invoice", status_code=status.HTTP_200_OK)
@limiter.limit(settings.RATE_LIMIT_LLM)
async def extract_invoice(
    request: Request,
    body: InvoiceExtractRequest,
    service: PromptService = Depends(get_prompt_service),
    current_user: User = Depends(get_current_user),
):
    """Extract structured invoice data from raw text. Returns validated JSON."""
    return await service.extract_invoice(
        text_content=body.text_content,
        user_id=current_user.id,
        model=body.model_name or settings.OLLAMA_MODEL,
    )
