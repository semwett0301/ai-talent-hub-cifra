"""Detection — recognise a link's kind before any crawling (Telegram); feeds are a port."""

from .telegram import is_telegram_link

__all__ = ["is_telegram_link"]
