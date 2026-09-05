"""Endpoints for legislative acts: list, get one, create."""

import uuid

from domain.entities.npa import NpaDTO
from fastapi import APIRouter, Depends, HTTPException, Query, status

from npa_service.application.dto.npa import NpaOut
from npa_service.application.errors import NpaAlreadyExistsError
from npa_service.application.services import NpaCatalog
from npa_service.deps import get_npa_catalog

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500

router = APIRouter(tags=["npa"])


@router.get("/", response_model=list[NpaOut])
async def list_npa(
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    catalog: NpaCatalog = Depends(get_npa_catalog),
) -> list[NpaOut]:
    acts = await catalog.list(limit, offset)
    return [NpaOut.model_validate(act) for act in acts]


@router.get("/{npa_id}", response_model=NpaOut)
async def get_npa(npa_id: uuid.UUID, catalog: NpaCatalog = Depends(get_npa_catalog)) -> NpaOut:
    act = await catalog.get(npa_id)
    if act is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="npa not found")

    return NpaOut.model_validate(act)


@router.post("/", response_model=NpaOut, status_code=status.HTTP_201_CREATED)
async def create_npa(payload: NpaDTO, catalog: NpaCatalog = Depends(get_npa_catalog)) -> NpaOut:
    try:
        act = await catalog.create(payload)
    except NpaAlreadyExistsError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(error)) from error

    return NpaOut.model_validate(act)
