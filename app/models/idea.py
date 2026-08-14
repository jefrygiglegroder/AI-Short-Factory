from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Idea(Base):
    __tablename__ = "ideas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(256), nullable=False)
    hook = Column(String(256), nullable=True)
    category = Column(String(128), nullable=True)
    concept = Column(Text, nullable=True)
    novelty_score = Column(Float, nullable=True)
    estimated_interest = Column(Float, nullable=True)
    status = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    account = relationship("Account", backref="ideas")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "account_id": self.account_id,
            "title": self.title,
            "hook": self.hook,
            "category": self.category,
            "concept": self.concept,
            "novelty_score": self.novelty_score,
            "estimated_interest": self.estimated_interest,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<Idea id={self.id} title={self.title}>"
