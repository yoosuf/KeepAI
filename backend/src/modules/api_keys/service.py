import hashlib
import secrets
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.api_keys.models import ApiKey


def generate_api_key() -> str:
    return f"ka_{secrets.token_hex(32)}"


def hash_api_key(key: str) -> str:
    return hashlib.sha512(key.encode()).hexdigest()


def preview_key(key: str) -> str:
    return key[:12] + "..."


class ApiKeyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_key(self, user_id: int, name: str, expires_at: Optional[datetime] = None) -> dict:
        full_key = generate_api_key()
        key_hash = hash_api_key(full_key)
        key_preview = preview_key(full_key)

        api_key = ApiKey(
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            key_preview=key_preview,
            expires_at=expires_at,
        )
        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)

        return {
            "id": api_key.id,
            "name": api_key.name,
            "key_preview": api_key.key_preview,
            "full_key": full_key,
            "created_at": api_key.created_at,
        }

    async def list_keys(self, user_id: int) -> List[ApiKey]:
        query = select(ApiKey).where(ApiKey.user_id == user_id).order_by(ApiKey.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def revoke_key(self, key_id: int, user_id: int) -> bool:
        query = select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id)
        result = await self.db.execute(query)
        key = result.scalars().first()
        if not key:
            return False
        key.is_active = False
        await self.db.commit()
        return True

    async def delete_key(self, key_id: int, user_id: int) -> bool:
        query = select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id)
        result = await self.db.execute(query)
        key = result.scalars().first()
        if not key:
            return False
        await self.db.delete(key)
        await self.db.commit()
        return True

    async def validate_key(self, key: str) -> Optional[ApiKey]:
        key_hash = hash_api_key(key)
        query = select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True))
        result = await self.db.execute(query)
        api_key = result.scalars().first()
        if not api_key:
            return None
        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            return None
        api_key.last_used_at = datetime.now(timezone.utc)
        await self.db.commit()
        return api_key
