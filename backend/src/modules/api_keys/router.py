from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.api_keys.schemas import ApiKeyCreate, ApiKeyCreateResponse, ApiKeyOut
from src.modules.api_keys.service import ApiKeyService
from src.modules.auth.models import User
from src.modules.auth.service import get_current_user

router = APIRouter()


def get_api_key_service(db: AsyncSession = Depends(get_db)) -> ApiKeyService:
    return ApiKeyService(db)


@router.get("/api-keys", response_model=list[ApiKeyOut])
async def list_api_keys(
    service: ApiKeyService = Depends(get_api_key_service),
    current_user: User = Depends(get_current_user),
):
    return await service.list_keys(user_id=current_user.id)


@router.post("/api-keys", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: ApiKeyCreate,
    service: ApiKeyService = Depends(get_api_key_service),
    current_user: User = Depends(get_current_user),
):
    return await service.create_key(
        user_id=current_user.id,
        name=body.name,
        expires_at=body.expires_at,
    )


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: int,
    service: ApiKeyService = Depends(get_api_key_service),
    current_user: User = Depends(get_current_user),
):
    deleted = await service.delete_key(key_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="API key not found")
