"""Endpoints for stored news: list the feed, open one, hide / unhide, escalate into an act."""

import uuid
from typing import Annotated

from common.entities.npa import NpaDTO
from common.schemas import News
from fastapi import APIRouter, Depends, HTTPException, Query, status

from news_service.application.dto.news import NewsOut, NewsQuery
from news_service.application.errors import NpaConflictError, NpaGatewayError
from news_service.application.services import NewsFeed, NpaEscalation
from news_service.deps import get_news_feed, get_npa_escalation

router = APIRouter(tags=["news"])


def _to_out_or_404(news: News | None) -> NewsOut:
    if news is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="news not found")

    return NewsOut.model_validate(news)


@router.get("/", response_model=list[NewsOut])
async def list_news(
    query: Annotated[NewsQuery, Query()], feed: NewsFeed = Depends(get_news_feed)
) -> list[NewsOut]:
    """Visible items by default (`visibility`); `q` searches title and text, `since` bounds the period."""
    return [NewsOut.model_validate(news) for news in await feed.list(query)]


@router.get("/{news_id}", response_model=NewsOut)
async def get_news(news_id: uuid.UUID, feed: NewsFeed = Depends(get_news_feed)) -> NewsOut:
    return _to_out_or_404(await feed.get(news_id))


@router.post("/{news_id}/dismiss", response_model=NewsOut)
async def dismiss_news(news_id: uuid.UUID, feed: NewsFeed = Depends(get_news_feed)) -> NewsOut:
    """Hide the item from the feed (`dismissed_at`); a repeat keeps the first moment."""
    return _to_out_or_404(await feed.dismiss(news_id))


@router.post("/{news_id}/restore", response_model=NewsOut)
async def restore_news(news_id: uuid.UUID, feed: NewsFeed = Depends(get_news_feed)) -> NewsOut:
    """Bring a hidden item back into the feed."""
    return _to_out_or_404(await feed.restore(news_id))


@router.post("/{news_id}/npa", response_model=NewsOut)
async def escalate_news(
    news_id: uuid.UUID,
    payload: NpaDTO | None = None,
    escalation: NpaEscalation = Depends(get_npa_escalation),
) -> NewsOut:
    """Flag the item as an alert and register it as an act in npa_service — atomically:
    if npa_service does not confirm, the flag is rolled back. Without a body the act is
    built from the news item itself."""
    try:
        news = await escalation.escalate(news_id, payload)
    except NpaConflictError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(error)) from error
    except NpaGatewayError as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error

    return _to_out_or_404(news)
