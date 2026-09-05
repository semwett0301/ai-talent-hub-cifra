"""Extraction — an already-fetched page's full article text, for the RSS collector."""

from .article import ExtractedArticle, extract_article

__all__ = [
    "ExtractedArticle",
    "extract_article",
]
