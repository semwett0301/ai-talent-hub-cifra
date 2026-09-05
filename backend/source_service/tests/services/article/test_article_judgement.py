from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from common.core.settings import WebCrawlSettings
from source_service.application.services.article import ArticleJudgement
from source_service.domain import (
    Article,
    ArticleContent,
    ArticleStatus,
    PublicationDate,
    RejectReason,
)

MOSCOW = ZoneInfo("Europe/Moscow")
URL = "https://example.test/news/1"


def dated(published_at: datetime, title: str | None = "Title") -> Article:
    content = ArticleContent(
        final_url=URL, title=title, text="x " * 100, word_count=100, fetched_at=datetime.now(MOSCOW)
    )
    publication = PublicationDate(value=published_at, source="json_ld", confidence=0.99)
    return Article(url=URL).with_content(content).with_publication(publication)


def test_fresh_titled_article_is_accepted():
    judgement = ArticleJudgement(WebCrawlSettings(days=3))
    [verdict] = judgement.run([dated(datetime.now(MOSCOW))])
    assert verdict.status is ArticleStatus.ACCEPTED


def test_old_article_is_out_of_window():
    judgement = ArticleJudgement(WebCrawlSettings(days=3))
    [verdict] = judgement.run([dated(datetime.now(MOSCOW) - timedelta(days=10))])
    assert verdict.rejection is RejectReason.OUT_OF_WINDOW


def test_untitled_article_is_rejected():
    judgement = ArticleJudgement(WebCrawlSettings(days=3))
    [verdict] = judgement.run([dated(datetime.now(MOSCOW), title=None)])
    assert verdict.rejection is RejectReason.NO_TITLE


def test_judgement_refuses_undated_articles():
    with pytest.raises(ValueError):
        ArticleJudgement(WebCrawlSettings()).run([Article(url=URL)])
