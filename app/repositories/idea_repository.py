from __future__ import annotations

from typing import List, Optional

from app.core.database import session_scope
from app.models.idea import Idea


def create_idea(
    account_id: int,
    title: str,
    hook: Optional[str] = None,
    category: Optional[str] = None,
    concept: Optional[str] = None,
    novelty_score: Optional[float] = None,
    estimated_interest: Optional[float] = None,
    status: Optional[str] = None,
):
    with session_scope() as s:
        idea = Idea(
            account_id=account_id,
            title=title,
            hook=hook,
            category=category,
            concept=concept,
            novelty_score=novelty_score,
            estimated_interest=estimated_interest,
            status=status,
        )
        s.add(idea)
        s.flush()
        s.refresh(idea)
        return idea


def list_ideas_for_account(account_id: int) -> List[Idea]:
    with session_scope() as s:
        return s.query(Idea).filter(Idea.account_id == account_id).order_by(Idea.id.asc()).all()


def get_idea(idea_id: int) -> Optional[Idea]:
    with session_scope() as s:
        return s.get(Idea, idea_id)
