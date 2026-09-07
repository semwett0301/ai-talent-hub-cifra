"""A news message with the stable database identity used by the LLM stages."""

import uuid
from dataclasses import dataclass

from common.entities.news import NewsDTO


@dataclass(frozen=True, slots=True)
class NewsTarget:
    news_id: uuid.UUID
    news: NewsDTO
