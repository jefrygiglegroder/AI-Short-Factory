from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime

from app.core.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(64), nullable=False)
    name = Column(String(128), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    niche = Column(String(128), nullable=True)
    content_style = Column(Text, nullable=True)  # JSON or free-form
    voice = Column(String(64), nullable=True)
    visual_style = Column(String(128), nullable=True)
    posting_schedule = Column(Text, nullable=True)  # JSON/text
    enabled = Column(Boolean, default=True, nullable=False)
    credentials_ref = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "platform": self.platform,
            "name": self.name,
            "description": self.description,
            "niche": self.niche,
            "content_style": self.content_style,
            "voice": self.voice,
            "visual_style": self.visual_style,
            "posting_schedule": self.posting_schedule,
            "enabled": self.enabled,
            "credentials_ref": self.credentials_ref,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<Account id={self.id} name={self.name} platform={self.platform}>"
