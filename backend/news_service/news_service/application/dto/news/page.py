"""One page of the feed plus how many items match in total — what the list endpoint returns."""

from pydantic import BaseModel

from news_service.application.dto.news.out import NewsOut


class NewsPage(BaseModel):
    items: list[NewsOut]
    # Every item matching the same filters, regardless of `limit` / `offset`.
    total: int
