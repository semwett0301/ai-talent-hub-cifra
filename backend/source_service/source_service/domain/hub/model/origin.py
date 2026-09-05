"""Which discovery step produced a hub."""

from enum import StrEnum


class HubOrigin(StrEnum):
    LISTING = "listing"  # the LLM classifier confirmed it is a listing page
    ADAPTIVE = "adaptive"  # found by the adaptive crawl (fallback)
    BEST_FIRST = "best_first"  # found by the best-first deep crawl (fallback)
    SEED = "seed"  # the home page, used when nothing else was found
