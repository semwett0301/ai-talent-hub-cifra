"""CRUD endpoints for sources."""

from fastapi import APIRouter, Depends, HTTPException, status

from source_service.application.dto.source import SourceCreate, SourceOut, SourceUpdate
from source_service.application.services import SourceService
from source_service.deps import get_source_service

router = APIRouter(tags=["sources"])


async def _get_or_404(service: SourceService, source_id: int):
    source = await service.get(source_id)
    if source is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="source not found")
    return source


@router.get("/", response_model=list[SourceOut])
async def list_sources(service: SourceService = Depends(get_source_service)) -> list[SourceOut]:
    return await service.list()


@router.post("/", response_model=SourceOut, status_code=status.HTTP_201_CREATED)
async def create_source(
    payload: SourceCreate, service: SourceService = Depends(get_source_service)
) -> SourceOut:
    return await service.create(payload)


@router.get("/{source_id}", response_model=SourceOut)
async def get_source(
    source_id: int, service: SourceService = Depends(get_source_service)
) -> SourceOut:
    return await _get_or_404(service, source_id)


@router.patch("/{source_id}", response_model=SourceOut)
async def update_source(
    source_id: int,
    payload: SourceUpdate,
    service: SourceService = Depends(get_source_service),
) -> SourceOut:
    source = await _get_or_404(service, source_id)
    return await service.update(source, payload)


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: int, service: SourceService = Depends(get_source_service)
) -> None:
    source = await _get_or_404(service, source_id)
    await service.delete(source)
