import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from common.entities.news import SourceType
from common.entities.source import SourceReliability
from common.schemas import Source
from source_service.domain import (
    Article,
    ArticleContent,
    ArticleStatus,
    BodyRequirement,
    PublicationDate,
    RejectReason,
)

MOSCOW = ZoneInfo("Europe/Moscow")
URL = "https://example.test/news/2026/09/04/release"


def content(title: str | None = "Release", canonical: str | None = None) -> ArticleContent:
    return ArticleContent(
        final_url=URL,
        canonical_url=canonical,
        title=title,
        text="word " * 100,
        word_count=100,
        fetched_at=datetime(2026, 9, 4, 12, tzinfo=MOSCOW),
    )


def publication() -> PublicationDate:
    return PublicationDate(
        value=datetime(2026, 9, 4, 10, tzinfo=MOSCOW),
        source="open_graph",
        confidence=0.98,
    )


def test_article_advances_one_stage_per_step_and_stays_immutable():
    discovered = Article(url=URL, title_hint="Card title")
    fetched = discovered.with_content(content())
    dated = fetched.with_publication(publication())
    accepted = dated.accept()

    assert discovered.status is ArticleStatus.DISCOVERED
    assert fetched.status is ArticleStatus.FETCHED
    assert dated.status is ArticleStatus.DATED
    assert accepted.status is ArticleStatus.ACCEPTED
    assert discovered.content is None  # the original was not mutated


def test_title_falls_back_from_page_title_to_card_text():
    article = Article(url=URL, title_hint="Card title")
    assert article.title == "Card title"
    assert article.with_content(content(title="Page title")).title == "Page title"
    assert article.with_content(content(title=None)).title == "Card title"


def test_identity_prefers_the_declared_canonical_url():
    discovered = Article(url=URL)
    assert discovered.identity == URL
    fetched = discovered.with_content(content(canonical="https://example.test/news/release"))
    assert fetched.identity == "https://example.test/news/release"
    assert discovered.with_content(content()).identity == URL


def test_body_requirement_is_a_plain_threshold():
    requirement = BodyRequirement(min_words=80)
    assert requirement.accepts(80)
    assert not requirement.accepts(79)


def test_reject_records_the_reason():
    rejected = Article(url=URL).reject(RejectReason.NO_DATE)
    assert rejected.status is ArticleStatus.REJECTED
    assert rejected.rejection is RejectReason.NO_DATE


def test_accept_requires_content_date_and_title():
    with pytest.raises(ValueError):
        Article(url=URL).accept()
    with pytest.raises(ValueError):
        Article(url=URL).with_content(content(title=None)).with_publication(publication()).accept()


def test_only_an_accepted_article_becomes_news():
    source = Source(
        id=uuid.uuid4(),
        name="Example",
        link="https://example.test",
        type=SourceType.WEB,
        reliability=SourceReliability.MEDIUM,
    )
    dated = Article(url=URL).with_content(content()).with_publication(publication())

    with pytest.raises(ValueError):
        dated.to_news_dto(source)

    news = dated.accept().to_news_dto(source)
    assert news.url == URL
    assert news.source_type is SourceType.WEB
    assert news.source_reliability is SourceReliability.MEDIUM
    assert news.published_at == publication().value
    assert news.source_id == source.id
    assert news.title == content().title
    assert news.text == content().text
