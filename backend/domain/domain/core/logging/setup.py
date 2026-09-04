"""Logging setup using the standard library."""

import logging

from domain.core.settings import settings

# Transport/protocol libraries whose DEBUG output is a firehose: aiormq/pamqp print
# every AMQP frame, aio_pika every published message, pyrogram every raw MTProto
# update (a user session gets them for every chat the account is in), urllib3 /
# charset_normalizer every request and encoding probe, newspaper / readability every
# DOM candidate they score. Their INFO is still useful (connect/disconnect), so they
# are capped, not silenced.
NOISY_LOGGERS = (
    "aio_pika",
    "aiormq",
    "pamqp",
    "pyrogram",
    "httpx",
    "httpcore",
    "urllib3",
    "charset_normalizer",
    "newspaper",
    "readability",
)
NOISY_LOGGER_LEVEL = logging.INFO

# Libraries that chatter at INFO on every call (news-please re-initialises its
# extractor pipeline per article and announces each stage) — capped at WARNING.
CHATTY_LOGGERS = ("newsplease",)
CHATTY_LOGGER_LEVEL = logging.WARNING


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    for logger_name in NOISY_LOGGERS:
        logging.getLogger(logger_name).setLevel(NOISY_LOGGER_LEVEL)

    for logger_name in CHATTY_LOGGERS:
        logging.getLogger(logger_name).setLevel(CHATTY_LOGGER_LEVEL)


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name)
