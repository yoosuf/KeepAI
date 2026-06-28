from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str
    role: str = "user"  # Optional during registration, defaults to user


class UserResponse(UserBase):
    id: int
    is_active: bool
    role: str

    @field_validator("role", mode="before")
    @classmethod
    def extract_role_name(cls, v):
        if hasattr(v, "name"):
            return v.name
        return v

    model_config = ConfigDict(from_attributes=True)
