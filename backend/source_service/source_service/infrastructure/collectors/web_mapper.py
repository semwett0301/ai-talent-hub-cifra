"""Mapping from crawler application records to the shared news contract."""

from typing import Any

from domain.entities.news import NewsDTO, SourceType
from domain.schemas import Source

from source_service.application.web_crawl.models import ArticleRecord


def to_news_dto(source: Source, article: ArticleRecord) -> NewsDTO:
    payload = article.model_dump(mode="json")
    raw: dict[str, Any] = {
        "title": article.title,
        "canonical_url": article.canonical_url,
        "author": article.author,
        "section": article.section,
        "language": article.language,
        "description": article.description,
        "image_url": article.image_url,
        "modified_at": payload["modified_at"],
        "fetched_at": payload["fetched_at"],
        "word_count": article.word_count,
        "date_source": article.date_source,
        "date_confidence": article.date_confidence,
        "date_evidence": article.date_evidence,
        "article": payload,
        "collector": {"name": "crawl4ai", "source_id": str(source.id)},
    }
    return NewsDTO(
        source_link=source.link,
        source_type=SourceType.WEB,
        source_reliability=source.reliability,
        url=article.url,
        text=article.text,
        published_at=article.published_at,
        raw=raw,
    )
