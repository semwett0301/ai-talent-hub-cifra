"""Thin HTTP endpoints for the tracked NPA registry."""

import uuid

from common.schemas import Npa, NpaVersion
from fastapi import APIRouter, Depends, HTTPException, Query, status

from npa_service.application.dto.npa import NpaCreate, NpaDetailOut, NpaOut, NpaVersionOut
from npa_service.application.errors import (
    InvalidNpaPageError,
    InvalidNpaUrlError,
    NpaAlreadyExistsError,
    NpaDocumentError,
    NpaSourceUnavailableError,
)
from npa_service.application.services import NpaCatalog, NpaRegistration
from npa_service.deps import get_npa_catalog, get_npa_registration

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500

router = APIRouter(tags=["npa"])


@router.get("/", response_model=list[NpaOut])
async def list_npa(
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    catalog: NpaCatalog = Depends(get_npa_catalog),
) -> list[NpaOut]:
    acts = await catalog.list_all(limit, offset)
    return [NpaOut.model_validate(act) for act in acts]


@router.get("/{npa_id}", response_model=NpaDetailOut)
async def get_npa(
    npa_id: uuid.UUID, catalog: NpaCatalog = Depends(get_npa_catalog)
) -> NpaDetailOut:
    act = await catalog.get(npa_id)
    if act is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="npa not found")

    versions = await catalog.list_versions(npa_id)
    return _details(act, versions)


@router.post("/", response_model=NpaDetailOut, status_code=status.HTTP_201_CREATED)
async def create_npa(
    payload: NpaCreate,
    registration: NpaRegistration = Depends(get_npa_registration),
    catalog: NpaCatalog = Depends(get_npa_catalog),
) -> NpaDetailOut:
    try:
        act = await registration.register(str(payload.url))
    except NpaAlreadyExistsError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(error)) from error
    except (InvalidNpaUrlError, InvalidNpaPageError, NpaDocumentError) as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except NpaSourceUnavailableError as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error

    versions = await catalog.list_versions(act.id)
    return _details(act, versions)


def _details(act: Npa, versions: list[NpaVersion]) -> NpaDetailOut:
    current = NpaOut.model_validate(act).model_dump()
    history = [NpaVersionOut.model_validate(version) for version in versions]
    return NpaDetailOut(**current, versions=history)
