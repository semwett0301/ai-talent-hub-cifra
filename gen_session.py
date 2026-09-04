"""One-time generator for TELEGRAM_SESSION.

Logs your Telegram user account in interactively (phone -> code -> 2FA if set)
and prints the session string to paste into .env. Nothing is written to disk
(in_memory=True) — the printed string is the only artifact.

Run from the repo root:

    uv run --project backend python gen_session.py

Reads TELEGRAM_API_ID / TELEGRAM_API_HASH from the environment or the repo-root
.env if present; otherwise it asks for them.
"""

import asyncio
import os
from pathlib import Path

from pyrogram.client import Client

ENV_FILE = Path(__file__).resolve().parent / ".env"


def _read_env(key: str) -> str | None:
    from_environ = os.environ.get(key)
    if from_environ:
        return from_environ

    if not ENV_FILE.exists():
        return None

    for line in ENV_FILE.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith(f"{key}="):
            return stripped.split("=", 1)[1].strip() or None
    return None


def _resolve(key: str, prompt: str) -> str:
    return _read_env(key) or input(prompt).strip()


async def main() -> None:
    api_id = int(_resolve("TELEGRAM_API_ID", "api_id: "))
    api_hash = _resolve("TELEGRAM_API_HASH", "api_hash: ")

    async with Client(
        "gen_session", api_id=api_id, api_hash=api_hash, in_memory=True
    ) as app:
        session_string = await app.export_session_string()
        me = await app.get_me()

    print(f"\nLogged in as: {me.first_name} (@{me.username}) id={me.id}")
    print("\n--- paste into .env ---")
    print(f"TELEGRAM_SESSION={session_string}")


asyncio.run(main())
