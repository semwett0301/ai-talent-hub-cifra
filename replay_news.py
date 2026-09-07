"""One-off: replay the stored news through the whole pipeline, with a known alert sample on top.

Runs inside the `news_service` container (RabbitMQ is not published to the host):

    docker compose cp replay_news.py news_service:/tmp/replay_news.py
    docker compose exec -T news_service python /tmp/replay_news.py dump /tmp/news_dump.json
    docker compose cp news_service:/tmp/news_dump.json news_dump.json
    docker compose exec -T news_service python /tmp/replay_news.py replay /tmp/news_dump.json
    docker compose exec -T news_service python /tmp/replay_news.py inspect --expect 538 --wait 1800

`dump` writes every `news` row as a `NewsDTO` (newest first). `replay` puts the Vedomosti
sample first as the newest item, deletes every `news` row (state and rankings cascade), and
publishes the list to the `news` exchange. `inspect` polls the DB until the batch has been
summarized, clustered and ranked, then prints what the pipeline produced.
"""

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import aio_pika
from common.core.db import async_session_factory
from common.core.settings import settings
from common.entities.news import NewsDTO, routing_key
from common.schemas import News, Source
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

SAMPLE_SOURCE_LINK_PATTERN = "%vedomosti%"
SAMPLE_URL = (
    "https://www.vedomosti.ru/technology/articles/2026/09/04/"
    "1226133-dlya-podklyuchaemih-k-gossistemam-servisov-usilyat-zaschitu"
)
SAMPLE_TITLE = "Для подключаемых к госсистемам сервисов усилят защиту"
SAMPLE_EXCERPT = (
    "За безопасностью виртуальных и облачных сред проследят силовые структуры"
)
SAMPLE_TEXT = (
    "ФСБ распространила требования по криптографической защите на внешние облачные сервисы и "
    "аппаратную часть, которые напрямую в состав госинформсистем (ГИС) не входят, но "
    "обеспечивают их работу. Ранее требования к применению сертифицированной криптографии "
    "распространялись только на саму ГИС и входящие в нее компоненты. Это следует из приказа "
    "ФСБ № 321 от 22 августа, опубликованного 31 августа.\n\n"
    "Специальные правила для подключаемых через сеть внешних сервисов появились после принятия "
    "закона № 568-ФЗ от 29 декабря 2025 г. (регулирует порядок создания госинформсистем и "
    "вводит обязанности для операторов). После этого правительство 18 августа 2026 г. приняло "
    "постановление № 1024, которое обязало размещать компоненты таких сервисов в России, "
    "разграничивать ответственность заказчика и поставщика в контракте, обеспечивать резервное "
    "копирование данных и сообщать об инцидентах. Эти правила вступили в силу 1 сентября. "
    "Приказ ФСБ дополняет их требованиями к криптографической защите."
)
SAMPLE_TAGS = ["Технологии"]
POLL_SECONDS = 20
PROGRESS_SQL = """
select
  (select count(*) from news)                                             as news,
  (select count(*) from news_event_state where summary is not null)      as summarized,
  (select count(*) from news_event_state where summary_embedding is not null) as embedded,
  (select count(*) from news_event_state where event_cluster_id is not null)  as clustered,
  (select count(*) from news_cluster_ranking)                             as ranked,
  (select count(*) from news where is_alert)                              as alerts
"""


def _to_dto(row: News) -> NewsDTO:
    return NewsDTO(
        schema_version=row.schema_version,
        source_id=row.source_id,
        source_link=row.source_link,
        source_name=row.source_name,
        source_type=row.source_type,
        source_reliability=row.source_reliability,
        source_tags=list(row.source_tags),
        url=row.url,
        title=row.title,
        text=row.text,
        excerpt=row.excerpt,
        published_at=row.published_at,
        updated_at=row.updated_at,
    )


async def dump(path: Path) -> None:
    async with async_session_factory() as session:
        rows = (
            (
                await session.execute(
                    select(News).order_by(
                        News.published_at.desc().nulls_last(), News.created_at.desc()
                    )
                )
            )
            .scalars()
            .all()
        )
    items = [_to_dto(row).model_dump(mode="json") for row in rows]
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), "utf-8")
    print(f"dumped {len(items)} news -> {path}")


async def _sample_source(session: AsyncSession) -> Source:
    source = (
        await session.execute(
            select(Source).where(Source.link.ilike(SAMPLE_SOURCE_LINK_PATTERN))
        )
    ).scalar_one_or_none()
    if source is None:
        raise SystemExit(
            "no Vedomosti source in `source`; the sample needs an existing source_id"
        )
    return source


def _sample(source: Source) -> NewsDTO:
    return NewsDTO.for_source(
        source,
        url=SAMPLE_URL,
        title=SAMPLE_TITLE,
        text=SAMPLE_TEXT,
        excerpt=SAMPLE_EXCERPT,
        published_at=datetime.now(UTC),
        source_tags=SAMPLE_TAGS,
    )


def _load(path: Path) -> list[NewsDTO]:
    return [
        NewsDTO.model_validate(item) for item in json.loads(path.read_text("utf-8"))
    ]


async def _publish(items: list[NewsDTO]) -> None:
    connection = await aio_pika.connect_robust(settings.rabbit.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            settings.rabbit.news_exchange, aio_pika.ExchangeType.TOPIC, durable=True
        )
        for item in items:
            message = aio_pika.Message(
                item.model_dump_json().encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            await exchange.publish(message, routing_key=routing_key(item.source_type))
    print(f"published {len(items)} news -> exchange={settings.rabbit.news_exchange}")


async def replay(path: Path) -> None:
    stored = [item for item in _load(path) if item.url != SAMPLE_URL]
    async with async_session_factory() as session:
        sample = _sample(await _sample_source(session))
        deleted = (await session.execute(text("delete from news"))).rowcount
        await session.commit()
    print(f"deleted {deleted} news rows (event state and rankings cascaded)")

    items = [sample, *stored]
    print(f"first item: {items[0].title!r} published_at={items[0].published_at}")
    await _publish(items)


async def _progress(session: AsyncSession) -> dict[str, int]:
    row = (await session.execute(text(PROGRESS_SQL))).one()
    return dict(row._mapping)


def _is_done(progress: dict[str, int], expected: int) -> bool:
    return progress["news"] >= expected and progress["clustered"] >= expected


async def _wait(expected: int, wait_seconds: int) -> None:
    deadline = asyncio.get_running_loop().time() + wait_seconds
    while True:
        async with async_session_factory() as session:
            progress = await _progress(session)
        print(f"{datetime.now(UTC):%H:%M:%S} progress: {progress}")
        if (
            _is_done(progress, expected)
            or asyncio.get_running_loop().time() >= deadline
        ):
            return
        await asyncio.sleep(POLL_SECONDS)


async def _print_rows(session: AsyncSession, title: str, sql: str) -> None:
    rows = (await session.execute(text(sql))).all()
    print(f"\n== {title} ({len(rows)}) ==")
    for row in rows:
        print("  " + " | ".join(str(value) for value in row))


async def _report() -> None:
    async with async_session_factory() as session:
        await _print_rows(
            session,
            "sample row",
            f"""
            select n.is_alert, s.primary_event_found, s.event_cluster_id = n.id as is_head,
                   r.relevance_score, r.category, r.member_count, s.summary
            from news n
            left join news_event_state s on s.news_id = n.id
            left join news_cluster_ranking r on r.cluster_id = coalesce(s.event_cluster_id, n.id)
            where n.url = '{SAMPLE_URL}'
            """,
        )
        await _print_rows(
            session,
            "alerts",
            "select source_name, published_at, title, url from news where is_alert "
            "order by published_at desc nulls last limit 30",
        )
        await _print_rows(
            session,
            "clusters with more than one member",
            """
            select r.cluster_id, r.member_count, r.category, round(r.relevance_score) as score,
                   n.title
            from news_cluster_ranking r join news n on n.id = r.cluster_id
            where r.member_count > 1 order by r.member_count desc, r.relevance_score desc limit 15
            """,
        )
        await _print_rows(
            session,
            "ranking by category",
            "select category, count(*), round(avg(relevance_score)) as avg_score "
            "from news_cluster_ranking group by category order by 3 desc",
        )
        await _print_rows(
            session,
            "top relevance",
            "select round(r.relevance_score) as score, r.category, n.source_name, n.title "
            "from news_cluster_ranking r join news n on n.id = r.cluster_id "
            "order by r.relevance_score desc limit 10",
        )


async def inspect(expected: int, wait_seconds: int) -> None:
    await _wait(expected, wait_seconds)
    await _report()


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("dump").add_argument("path", type=Path)
    commands.add_parser("replay").add_argument("path", type=Path)
    inspect_parser = commands.add_parser("inspect")
    inspect_parser.add_argument("--expect", type=int, required=True)
    inspect_parser.add_argument("--wait", type=int, default=1800)
    return parser.parse_args(argv)


def main(argv: list[str]) -> None:
    args = _parse_args(argv)
    if args.command == "dump":
        asyncio.run(dump(args.path))
    elif args.command == "replay":
        asyncio.run(replay(args.path))
    else:
        asyncio.run(inspect(args.expect, args.wait))


if __name__ == "__main__":
    main(sys.argv[1:])
