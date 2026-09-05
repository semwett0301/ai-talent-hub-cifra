"""Telegram-link recognition — checked first, before any crawling."""

from urllib.parse import urlparse

TELEGRAM_URI_SCHEME = "tg"
TELEGRAM_HOSTS = {"t.me", "telegram.me"}


def is_telegram_link(link: str) -> bool:
    """True for `tg://...` deep links (host carries no meaning there) or
    `https://t.me/...` / `https://telegram.me/...` links."""
    parsed = urlparse(link)
    if parsed.scheme == TELEGRAM_URI_SCHEME:
        return True

    return parsed.hostname in TELEGRAM_HOSTS
