from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.auth.models import User
from src.modules.auth.schemas import UserResponse
from src.modules.auth.service import PermissionChecker
from src.modules.prompts.models import Prompt
from src.modules.prompts.schemas import PromptResponse

router = APIRouter()


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(PermissionChecker("users:read")),
    db: AsyncSession = Depends(get_db),
):
    """Admin only: List all users"""
    query = select(User).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/all-prompts", response_model=List[PromptResponse])
async def get_all_prompts(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(PermissionChecker("prompts:read_all")),
    db: AsyncSession = Depends(get_db),
):
    """Admin only: View prompts from all users for auditing"""
    query = select(Prompt).order_by(Prompt.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
