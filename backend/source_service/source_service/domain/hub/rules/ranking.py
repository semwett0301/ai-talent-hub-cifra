"""Ranking hubs by how listing-like they are — one hub per URL, the best sighting wins."""

from collections.abc import Iterable

from source_service.domain.hub.hub import Hub

from .scoring import HUB_SCORER


def hub_score(hub: Hub) -> float:
    return HUB_SCORER.score(hub).value


def rank_hubs(hubs: Iterable[Hub]) -> list[Hub]:
    return sorted(hubs, key=hub_score, reverse=True)


def merge_hubs(hubs: Iterable[Hub]) -> list[Hub]:
    """The same URL seen several times (with different titles or excerpts) is one hub;
    keep the sighting that scores best, ranked."""
    best: dict[str, Hub] = {}
    for hub in hubs:
        previous = best.get(hub.url)
        if previous is None or hub_score(hub) > hub_score(previous):
            best[hub.url] = hub
    return rank_hubs(best.values())


def select_hubs(hubs: Iterable[Hub], min_score: float) -> list[Hub]:
    """Hub-like enough to be read: `merge_hubs` over the sightings above `min_score`."""
    return merge_hubs(hub for hub in hubs if hub_score(hub) >= min_score)
