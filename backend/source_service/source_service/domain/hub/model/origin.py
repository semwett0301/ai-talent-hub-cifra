"""Which discovery step produced a hub."""

from enum import StrEnum


class HubOrigin(StrEnum):
    LISTING = "listing"  # the LLM classifier confirmed it is a listing page
    SEED = "seed"  # the home page, used when nothing else was found
