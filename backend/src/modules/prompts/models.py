from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.core.database import Base


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # Make nullable for now to support old records or optional auth

    prompt_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=True)
    model_name = Column(String, default="llama3")

    # Metadata
    processing_time_ms = Column(Integer, nullable=True)
    meta_data = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Use string forward reference to avoid circular import with Auth module
    owner = relationship("src.modules.auth.models.User", back_populates="prompts")

    def __repr__(self):
        return f"<Prompt(id={self.id}, created_at={self.created_at})>"
