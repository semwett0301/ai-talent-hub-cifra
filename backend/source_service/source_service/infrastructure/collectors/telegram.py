"""Telegram collector (push) — a PushCollector over a kurigram user session.

Subscribes to public channels via MTProto: joins each channel and, on every new
post, maps it to a `NewsItem` and publishes it to RabbitMQ through the injected
`NewsPublisher`. Degrades to a no-op when API credentials or an authorized
session are absent (so the service still boots without Telegram configured).

kurigram (PyPI: `kurigram`) is an actively maintained Pyrogram fork; it is
imported as `pyrogram`, unchanged. Unlike Telethon, pyrogram has no
`is_user_authorized()` pre-check — an unresumeable session falls back to
interactive `input()` prompts inside `Client.start()`. `start()` below never
calls it without a session string, and catches `RPCError` for a stale one, so
a headless container never blocks on stdin.
"""

from common.core.logging import get_logger
from pyrogram import filters
from pyrogram.client import Client
from pyrogram.errors import RPCError
from pyrogram.handlers import MessageHandler
from pyrogram.types import Chat, Message

from source_service.application.ports import NewsPublisher, PushCollector
from source_service.domain.entities import NewsItem
from source_service.domain.schemas import Source

TELEGRAM_BASE_URL = "https://t.me"
CLIENT_SESSION_NAME = "source_service"

logger = get_logger(__name__)


def _message_url(chat: Chat, message: Message) -> str:
    # Public channels expose a @username; private ones use the /c/<id> form.
    if chat.username:
        return f"{TELEGRAM_BASE_URL}/{chat.username}/{message.id}"

    return f"{TELEGRAM_BASE_URL}/c/{chat.id}/{message.id}"


def _to_news_item(chat: Chat, message: Message) -> NewsItem:
    return NewsItem(
        url=_message_url(chat, message),
        text=message.text or message.caption or "",
        published_at=message.date,
        raw={"chat_id": chat.id, "message_id": message.id},
    )


class TelegramCollector(PushCollector):
    def __init__(
        self,
        publisher: NewsPublisher,
        api_id: int | None,
        api_hash: str | None,
        session: str,
    ) -> None:
        self.__publisher = publisher
        self.__client = self.__build_client(api_id, api_hash, session)

        # Marked chat id (matches `message.chat.id`) → the Source it belongs to.
        self.__sources: dict[int, Source] = {}

    @staticmethod
    def __build_client(api_id: int | None, api_hash: str | None, session: str) -> Client | None:
        if not api_id or not api_hash or not session:
            return None

        return Client(
            CLIENT_SESSION_NAME,
            api_id=api_id,
            api_hash=api_hash,
            session_string=session,
            in_memory=True,
        )

    async def start(self) -> None:
        """Connect the user session and register the single new-post handler."""
        if self.__client is None:
            logger.warning("telegram creds absent; collector disabled")
            return

        try:
            await self.__client.start()
        except RPCError:
            logger.warning("telegram session not authorized; collector disabled")
            self.__client = None
            return

        self.__client.add_handler(MessageHandler(self.__on_message, filters.channel))
        logger.info("telegram client started")

    async def stop(self) -> None:
        if self.__client is not None:
            await self.__client.stop()

    async def subscribe(self, source: Source) -> None:
        if self.__client is None:
            return

        await self.__client.join_chat(source.link)
        chat = await self.__client.get_chat(source.link)

        if chat is None or chat.id is None:
            logger.warning("telegram chat not found: %s", source.link)
            return

        self.__sources[chat.id] = source
        logger.info("telegram subscribed: %s", source.link)

    async def unsubscribe(self, source: Source) -> None:
        if self.__client is None:
            return

        chat = await self.__client.get_chat(source.link)
        if chat is not None and chat.id is not None:
            self.__sources.pop(chat.id, None)

        await self.__client.leave_chat(source.link)
        logger.info("telegram unsubscribed: %s", source.link)

    async def __on_message(self, _: Client, message: Message) -> None:
        if message.chat is None or message.chat.id is None:
            return

        source = self.__sources.get(message.chat.id)
        if source is None:
            return

        item = _to_news_item(message.chat, message)
        await self.__publisher.publish_news(source.id, source.type, [item])
