"""Minimal CLI for AI Short Factory (Phase 1).

Commands implemented in this phase:
- hardware: show detected hardware (GPU/CPU/disk) using app.core.hardware

This file intentionally keeps the CLI small and dependency-free so it can be
expanded reliably in future phases.
"""
from __future__ import annotations

import argparse
import sys
from typing import Any


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="ai-short-factory")
    parser.add_argument("--version", action="store_true", help="Show package version and exit")

    subparsers = parser.add_subparsers(dest="command", required=False)

    sp_hw = subparsers.add_parser("hardware", help="Show detected hardware (GPU/CPU/disk)")
    sp_hw.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of human-friendly text")

    # Placeholders for future Phase 1 commands (not implemented here):
    # subparsers.add_parser("account", help="Account management commands (create/list)")
    # subparsers.add_parser("dashboard", help="Launch GUI dashboard")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    # lightweight import to avoid importing heavy modules at top-level
    if args.version:
        try:
            # avoid importing the package if it's not available on path
            from app import __version__
        except Exception:
            __version__ = "(unknown)"
        else:
            __version__ = __version__
        print(f"AI Short Factory {__version__}")
        return 0

    if args.command == "hardware":
        try:
            from app.core.hardware import get_system_info, pretty_print_hardware
        except Exception as exc:
            print("Error: unable to import hardware module:", exc, file=sys.stderr)
            return 2

        if args.json:
            import json

            print(json.dumps(get_system_info(), indent=2))
        else:
            print(pretty_print_hardware())
        return 0

    # No command: show help
    print("AI Short Factory - Phase 1 (minimal CLI)\n")
    print("Use 'hardware' to inspect system hardware. Example: python -m app hardware\n")
    print("Run with --version to see package version.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
