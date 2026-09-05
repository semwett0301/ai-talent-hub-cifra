"""Endpoints for stored news: list all, dismiss one, escalate one into a legislative act."""

import uuid

from common.entities.npa import NpaDTO
from common.schemas import News
from fastapi import APIRouter, Depends, HTTPException, Query, status

from news_service.application.dto.news import NewsOut
from news_service.application.errors import NpaConflictError, NpaGatewayError
from news_service.application.services import NewsFeed, NpaEscalation
from news_service.deps import get_news_feed, get_npa_escalation

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500

router = APIRouter(tags=["news"])


def _to_out_or_404(news: News | None) -> NewsOut:
    if news is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="news not found")

    return NewsOut.model_validate(news)


@router.get("/", response_model=list[NewsOut])
async def list_news(
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    feed: NewsFeed = Depends(get_news_feed),
) -> list[NewsOut]:
    items = await feed.list(limit, offset)
    return [NewsOut.model_validate(news) for news in items]


@router.post("/{news_id}/dismiss", response_model=NewsOut)
async def dismiss_news(news_id: uuid.UUID, feed: NewsFeed = Depends(get_news_feed)) -> NewsOut:
    news = await feed.dismiss(news_id)
    return _to_out_or_404(news)


@router.post("/{news_id}/npa", response_model=NewsOut)
async def escalate_news(
    news_id: uuid.UUID,
    payload: NpaDTO,
    escalation: NpaEscalation = Depends(get_npa_escalation),
) -> NewsOut:
    """Dismiss the alert and register `payload` as an act in npa_service — atomically:
    if npa_service does not confirm, the alert stays undismissed."""
    try:
        news = await escalation.escalate(news_id, payload)
    except NpaConflictError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(error)) from error
    except NpaGatewayError as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error

    return _to_out_or_404(news)
