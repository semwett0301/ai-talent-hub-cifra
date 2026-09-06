"""Load and validate the packaged or operator-supplied company relevance profile."""

import json
from importlib import resources

from pydantic import BaseModel, Field, ValidationError

from news_service.domain.ranking import CompanyProfile, Facet

PROFILE_PACKAGE = "news_service.infrastructure.ranking"
DEFAULT_PROFILE_NAME = "company_profile.json"


class _FacetPayload(BaseModel):
    name: str
    description: str
    bm25_terms: list[str] = Field(default_factory=list)
    reranker_guidance: str = ""


class _CompanyPayload(BaseModel):
    name: str
    description: str
    facets: list[_FacetPayload]
    language: str = "ru"


def load_company_profile() -> CompanyProfile:
    try:
        payload = _CompanyPayload.model_validate(json.loads(_read_packaged_profile()))
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        raise ValueError(f"invalid news ranking profile: path={DEFAULT_PROFILE_NAME}") from error
    if not payload.facets:
        raise ValueError("news ranking profile must contain at least one facet")
    return CompanyProfile(
        payload.name,
        payload.description,
        tuple(_to_facet(facet) for facet in payload.facets),
        payload.language,
    )


def _read_packaged_profile() -> str:
    return resources.files(PROFILE_PACKAGE).joinpath(DEFAULT_PROFILE_NAME).read_text("utf-8")


def _to_facet(payload: _FacetPayload) -> Facet:
    return Facet(
        payload.name,
        payload.description,
        tuple(payload.bm25_terms),
        payload.reranker_guidance,
    )
