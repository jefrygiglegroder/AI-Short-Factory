from __future__ import annotations

from typing import List, Optional

from app.core.database import session_scope
from app.models.account import Account


def create_account(
    platform: str,
    name: str,
    description: Optional[str] = None,
    niche: Optional[str] = None,
    content_style: Optional[str] = None,
    voice: Optional[str] = None,
    visual_style: Optional[str] = None,
    posting_schedule: Optional[str] = None,
    enabled: bool = True,
    credentials_ref: Optional[str] = None,
):
    with session_scope() as s:
        acct = Account(
            platform=platform,
            name=name,
            description=description,
            niche=niche,
            content_style=content_style,
            voice=voice,
            visual_style=visual_style,
            posting_schedule=posting_schedule,
            enabled=enabled,
            credentials_ref=credentials_ref,
        )
        s.add(acct)
        s.flush()
        s.refresh(acct)
        return acct


def get_account(account_id: int):
    with session_scope() as s:
        return s.get(Account, account_id)


def list_accounts() -> List[Account]:
    with session_scope() as s:
        return s.query(Account).order_by(Account.id.asc()).all()
