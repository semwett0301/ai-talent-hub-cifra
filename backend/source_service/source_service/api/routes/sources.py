"""CRUD endpoints for sources."""

import uuid

from common.core.logging import get_logger
from common.schemas import Source
from fastapi import APIRouter, Depends, HTTPException, status

from source_service.application.dto.source import SourceCreate, SourceOut, SourceUpdate
from source_service.application.services.source import SourceService
from source_service.deps import get_source_service

logger = get_logger(__name__)

router = APIRouter(tags=["sources"])


async def _get_or_404(service: SourceService, source_id: uuid.UUID) -> Source:
    source = await service.get(source_id)
    if source is None:
        logger.warning("source not found: id=%s", source_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="source not found")

    return source


@router.get("/", response_model=list[SourceOut])
async def list_sources(service: SourceService = Depends(get_source_service)) -> list[SourceOut]:
    sources = await service.list()
    return [SourceOut.model_validate(source) for source in sources]


@router.post("/", response_model=SourceOut, status_code=status.HTTP_201_CREATED)
async def create_source(
    payload: SourceCreate, service: SourceService = Depends(get_source_service)
) -> SourceOut:
    created = await service.create(payload)
    return SourceOut.model_validate(created)


@router.get("/{source_id}", response_model=SourceOut)
async def get_source(
    source_id: uuid.UUID, service: SourceService = Depends(get_source_service)
) -> SourceOut:
    source = await _get_or_404(service, source_id)
    return SourceOut.model_validate(source)


@router.patch("/{source_id}", response_model=SourceOut)
async def update_source(
    source_id: uuid.UUID,
    payload: SourceUpdate,
    service: SourceService = Depends(get_source_service),
) -> SourceOut:
    source = await _get_or_404(service, source_id)
    updated = await service.update(source, payload)
    return SourceOut.model_validate(updated)


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: uuid.UUID, service: SourceService = Depends(get_source_service)
) -> None:
    source = await _get_or_404(service, source_id)
    await service.delete(source)
