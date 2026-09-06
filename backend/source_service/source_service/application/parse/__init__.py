"""Parse — pure text-in/structure-out logic, grouped by concern: `detection` (source-type
recognition), `extraction` (RSS article text) and `reading` (web-crawl date/listing/article
parsing)."""

from source_service.application.parse.detection import is_telegram_link
from source_service.application.parse.extraction import ExtractedArticle, extract_article
from source_service.application.parse.reading import (
    DateSource,
    PublicationDateSignal,
    article_body,
    choose_text_container,
    extract_html_metadata,
    extract_publication_date_signal,
    listing_cards,
    listing_llm_snapshot,
    next_listing_page,
    pagination_link,
    parse_date,
    word_count,
)

__all__ = [
    "DateSource",
    "ExtractedArticle",
    "PublicationDateSignal",
    "article_body",
    "choose_text_container",
    "extract_article",
    "extract_html_metadata",
    "extract_publication_date_signal",
    "is_telegram_link",
    "listing_cards",
    "listing_llm_snapshot",
    "next_listing_page",
    "pagination_link",
    "parse_date",
    "word_count",
]
