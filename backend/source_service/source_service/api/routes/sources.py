"""CRUD endpoints for sources."""

from fastapi import APIRouter, Depends, HTTPException, status

from source_service.application.dto.source import SourceCreate, SourceOut, SourceUpdate
from source_service.application.services import SourceService
from source_service.deps import get_source_service
from source_service.domain.schemas import Source

router = APIRouter(tags=["sources"])


async def _get_or_404(service: SourceService, link: str) -> Source:
    source = await service.get(link)
    if source is None:
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


@router.get("/{link:path}", response_model=SourceOut)
async def get_source(
    link: str, service: SourceService = Depends(get_source_service)
) -> SourceOut:
    source = await _get_or_404(service, link)
    return SourceOut.model_validate(source)


@router.patch("/{link:path}", response_model=SourceOut)
async def update_source(
    link: str,
    payload: SourceUpdate,
    service: SourceService = Depends(get_source_service),
) -> SourceOut:
    source = await _get_or_404(service, link)
    updated = await service.update(source, payload)
    return SourceOut.model_validate(updated)


@router.delete("/{link:path}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    link: str, service: SourceService = Depends(get_source_service)
) -> None:
    source = await _get_or_404(service, link)
    await service.delete(source)
