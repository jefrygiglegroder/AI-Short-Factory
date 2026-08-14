"""Module entrypoint so users can run: python -m app

This defers to app.main.main() which implements the CLI.
"""
from .main import main

if __name__ == "__main__":
    raise SystemExit(main())
