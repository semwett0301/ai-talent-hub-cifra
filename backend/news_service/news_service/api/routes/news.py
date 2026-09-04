"""Read endpoints for stored news: list all, dismiss one."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from news_service.application.dto.news import NewsOut
from news_service.application.services import NewsService
from news_service.deps import get_news_service

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500

router = APIRouter(tags=["news"])


@router.get("/", response_model=list[NewsOut])
async def list_news(
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    service: NewsService = Depends(get_news_service),
) -> list[NewsOut]:
    items = await service.list(limit, offset)
    return [NewsOut.model_validate(news) for news in items]


@router.post("/{news_id}/dismiss", response_model=NewsOut)
async def dismiss_news(
    news_id: uuid.UUID, service: NewsService = Depends(get_news_service)
) -> NewsOut:
    news = await service.dismiss(news_id)
    if news is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="news not found")

    return NewsOut.model_validate(news)
