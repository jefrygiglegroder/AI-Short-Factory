from __future__ import annotations

import argparse
import sys
from typing import Any

from app.repositories import account_repository


def register_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("account", help="Account management commands")
    sub = parser.add_subparsers(dest="account_cmd")

    p_create = sub.add_parser("create", help="Create a new account")
    p_create.add_argument("--platform", required=True)
    p_create.add_argument("--name", required=True)
    p_create.add_argument("--description", default=None)
    p_create.add_argument("--niche", default=None)
    p_create.add_argument("--voice", default=None)
    p_create.add_argument("--visual_style", default=None)
    p_create.set_defaults(func=_handle_create)

    p_list = sub.add_parser("list", help="List accounts")
    p_list.set_defaults(func=_handle_list)

    p_get = sub.add_parser("get", help="Get account by id")
    p_get.add_argument("id", type=int)
    p_get.set_defaults(func=_handle_get)


def _handle_create(args: argparse.Namespace) -> int:  # pragma: no cover - CLI flow
    acct = account_repository.create_account(
        platform=args.platform,
        name=args.name,
        description=args.description,
        niche=args.niche,
        voice=args.voice,
        visual_style=args.visual_style,
    )
    print(acct.to_dict())
    return 0


def _handle_list(args: argparse.Namespace) -> int:  # pragma: no cover - CLI flow
    accts = account_repository.list_accounts()
    for a in accts:
        print(a.to_dict())
    return 0


def _handle_get(args: argparse.Namespace) -> int:  # pragma: no cover - CLI flow
    a = account_repository.get_account(args.id)
    if not a:
        print(f"Account {args.id} not found", file=sys.stderr)
        return 2
    print(a.to_dict())
    return 0
