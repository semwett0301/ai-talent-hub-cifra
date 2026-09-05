"""Ranking hubs by how listing-like they are — one hub per URL, the best sighting wins."""

from collections.abc import Iterable

from source_service.domain.hub.hub import Hub

from .scoring import HUB_SCORER


def hub_score(hub: Hub) -> float:
    return HUB_SCORER.score(hub).value


def rank_hubs(hubs: Iterable[Hub]) -> list[Hub]:
    return sorted(hubs, key=hub_score, reverse=True)
