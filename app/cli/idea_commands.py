from __future__ import annotations

import argparse
import sys
from typing import Any

from app.repositories import idea_repository


def register_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("idea", help="Idea management commands")
    sub = parser.add_subparsers(dest="idea_cmd")

    p_create = sub.add_parser("create", help="Create a new idea for an account")
    p_create.add_argument("--account_id", type=int, required=True)
    p_create.add_argument("--title", required=True)
    p_create.add_argument("--hook", default=None)
    p_create.add_argument("--category", default=None)
    p_create.set_defaults(func=_handle_create)

    p_list = sub.add_parser("list", help="List ideas for an account")
    p_list.add_argument("--account_id", type=int, required=True)
    p_list.set_defaults(func=_handle_list)

    p_get = sub.add_parser("get", help="Get idea by id")
    p_get.add_argument("id", type=int)
    p_get.set_defaults(func=_handle_get)


def _handle_create(args: argparse.Namespace) -> int:  # pragma: no cover - CLI flow
    idea = idea_repository.create_idea(
        account_id=args.account_id,
        title=args.title,
        hook=args.hook,
        category=args.category,
    )
    print(idea.to_dict())
    return 0


def _handle_list(args: argparse.Namespace) -> int:  # pragma: no cover - CLI flow
    ideas = idea_repository.list_ideas_for_account(args.account_id)
    for i in ideas:
        print(i.to_dict())
    return 0


def _handle_get(args: argparse.Namespace) -> int:  # pragma: no cover - CLI flow
    i = idea_repository.get_idea(args.id)
    if not i:
        print(f"Idea {args.id} not found", file=sys.stderr)
        return 2
    print(i.to_dict())
    return 0
