"""Validate a headerless news table export and republish it through the news contract."""

import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import aio_pika
import pandas as pd
from pydantic import ValidationError

REPOSITORY_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPOSITORY_ROOT / "backend" / "common"))

from common.entities.news import NewsDTO, SourceType, routing_key  # noqa: E402

CSV_COLUMNS = (
    "id",
    "schema_version",
    "source_link",
    "source_type",
    "source_reliability",
    "url",
    "text",
    "published_at",
    "is_alert",
    "created_at",
    "source_id",
    "title",
    "excerpt",
    "updated_at",
    "source_name",
    "source_tags",
    "dismissed_at",
)
PREVIEW_COUNT = 3

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PublisherConfig:
    csv_path: Path
    rabbitmq_url: str | None
    exchange_name: str
    limit: int | None
    is_dry_run: bool


@dataclass(frozen=True)
class PreparedMessage:
    csv_row: int
    payload: dict[str, Any]


class DatasetError(RuntimeError):
    """A dataset or publisher configuration error safe to show to an operator."""


def _optional_text(value: Any) -> str | None:
    text = str(value)
    return text if text else None


def _optional_datetime(value: Any) -> Any | None:
    if value == "" or pd.isna(value):
        return None

    return pd.to_datetime(value).to_pydatetime()


def _parse_postgres_array(value: Any) -> list[str]:
    text = str(value)
    if text == "{}":
        return []
    if not text.startswith("{") or not text.endswith("}"):
        raise ValueError(f"invalid PostgreSQL array: {text!r}")

    return _split_postgres_array(text[1:-1])


def _split_postgres_array(content: str) -> list[str]:
    values: list[str] = []
    current: list[str] = []
    is_quoted = False
    is_escaped = False

    for character in content:
        if is_escaped:
            current.append(character)
            is_escaped = False
        elif character == "\\":
            is_escaped = True
        elif character == '"':
            is_quoted = not is_quoted
        elif character == "," and not is_quoted:
            values.append("".join(current))
            current = []
        else:
            current.append(character)

    if is_quoted or is_escaped:
        raise ValueError("unterminated quote or escape in PostgreSQL array")
    values.append("".join(current))
    return values


def row_to_message(row: pd.Series) -> dict[str, Any]:
    """Map one exported DB row to the shared RabbitMQ NewsDTO payload."""
    candidate = {
        "schema_version": int(row["schema_version"]),
        "source_id": row["source_id"],
        "source_link": str(row["source_link"]),
        "source_name": str(row["source_name"]),
        "source_type": row["source_type"],
        "source_reliability": row["source_reliability"],
        "source_tags": _parse_postgres_array(row["source_tags"]),
        "url": str(row["url"]),
        "title": str(row["title"]),
        "text": str(row["text"]),
        "excerpt": _optional_text(row["excerpt"]),
        "published_at": _optional_datetime(row["published_at"]),
        "updated_at": _optional_datetime(row["updated_at"]),
    }
    return NewsDTO.model_validate(candidate).model_dump(mode="json")


def _read_csv(csv_path: Path) -> pd.DataFrame:
    if not csv_path.is_file():
        raise DatasetError(f"CSV file not found: {csv_path}")

    frame = pd.read_csv(csv_path, header=None, keep_default_na=False)
    if frame.shape[1] != len(CSV_COLUMNS):
        raise DatasetError(
            f"CSV has {frame.shape[1]} columns; expected {len(CSV_COLUMNS)} headerless columns"
        )
    frame.columns = list(CSV_COLUMNS)
    return frame


def _prepare_messages(frame: pd.DataFrame, limit: int | None) -> list[PreparedMessage]:
    selected = frame if limit is None else frame.head(limit)
    messages: list[PreparedMessage] = []

    for index, row in selected.iterrows():
        csv_row = int(index) + 1
        try:
            payload = row_to_message(row)
        except (TypeError, ValueError, ValidationError) as error:
            raise DatasetError(f"CSV row {csv_row}: {error}") from error
        messages.append(PreparedMessage(csv_row, payload))

    return messages


def _show_preview(messages: list[PreparedMessage]) -> None:
    for message in messages[:PREVIEW_COUNT]:
        body = json.dumps(message.payload, ensure_ascii=False, separators=(",", ":"))
        logger.info("payload validated: csv_row=%d body=%s", message.csv_row, body)


def _to_amqp_message(payload: dict[str, Any]) -> aio_pika.Message:
    dto = NewsDTO.model_validate(payload)
    return aio_pika.Message(
        dto.model_dump_json().encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT
    )


async def _publish(config: PublisherConfig, messages: list[PreparedMessage]) -> int:
    if not config.rabbitmq_url:
        raise DatasetError(
            "RABBITMQ_URL or --rabbitmq-url is required unless --dry-run is used"
        )

    connection = await aio_pika.connect_robust(config.rabbitmq_url)
    try:
        channel = await connection.channel()
        exchange = await channel.get_exchange(config.exchange_name, ensure=True)
        return await _publish_all(exchange, messages)
    finally:
        await connection.close()


async def _publish_all(
    exchange: aio_pika.abc.AbstractExchange, messages: list[PreparedMessage]
) -> int:
    published = 0
    for message in messages:
        try:
            source_type = SourceType(message.payload["source_type"])
            await exchange.publish(
                _to_amqp_message(message.payload), routing_key(source_type)
            )
        except (aio_pika.AMQPException, TypeError, ValueError) as error:
            raise DatasetError(
                f"CSV row {message.csv_row}: publish failed: {error}"
            ) from error
        published += 1

    return published


def _positive_limit(value: str) -> int:
    limit = int(value)
    if limit < 1:
        raise argparse.ArgumentTypeError("limit must be greater than zero")
    return limit


def _parse_args() -> PublisherConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv-path", default=os.getenv("CSV_PATH", "news.csv"), type=Path
    )
    parser.add_argument("--rabbitmq-url", default=os.getenv("RABBITMQ_URL"))
    parser.add_argument("--exchange", default=os.getenv("NEWS_EXCHANGE", "news"))
    parser.add_argument("--limit", type=_positive_limit)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return PublisherConfig(
        args.csv_path, args.rabbitmq_url, args.exchange, args.limit, args.dry_run
    )


async def _run(config: PublisherConfig) -> None:
    frame = _read_csv(config.csv_path)
    messages = _prepare_messages(frame, config.limit)
    logger.info("dataset validated: path=%s rows=%d", config.csv_path, len(messages))

    if config.is_dry_run:
        _show_preview(messages)
        logger.info("dry run completed: messages=%d", len(messages))
        return

    published = await _publish(config, messages)
    logger.info(
        "dataset published: exchange=%s messages=%d", config.exchange_name, published
    )


def main() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    try:
        asyncio.run(_run(_parse_args()))
    except (
        DatasetError,
        aio_pika.AMQPException,
        OSError,
        pd.errors.ParserError,
    ) as error:
        logger.error("dataset publish failed: %s", error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
