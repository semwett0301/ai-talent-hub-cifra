"""`RabbitSettings` — the message bus and the exchange news travels on."""

from .base import SettingsTemplate


class RabbitSettings(SettingsTemplate):
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    news_exchange: str = "news"
