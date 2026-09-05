"""`Frontier` — which listing URLs of one site have already been fetched."""

from collections.abc import Iterator
from dataclasses import dataclass, field

from source_service.domain.urls import listing_identity


@dataclass
class Frontier:
    """Per-site discovery state: every URL identity is fetched at most once, and never more
    than `max_pages` across the whole site (0 = no cap). Fresh for every site crawl."""

    max_pages: int
    seen: set[str] = field(default_factory=set)

    def take(self, urls: list[str]) -> list[str]:
        """The URLs of `urls` nobody has fetched yet — recorded as seen by this very call,
        so the same page can never be handed out twice."""
        batch = list(self.__unseen(urls))
        self.seen.update(listing_identity(url) for url in batch)
        return batch

    def __unseen(self, urls: list[str]) -> Iterator[str]:
        """Pure selection: URLs whose identity is neither already seen nor a duplicate
        earlier in `urls`, stopping at the cap. Records nothing."""
        picked: set[str] = set()

        for url in urls:
            identity = listing_identity(url)
            if identity in self.seen or identity in picked:
                continue
            if self.max_pages and len(self.seen) + len(picked) >= self.max_pages:
                return

            picked.add(identity)
            yield url

    @property
    def pages_seen(self) -> int:
        return len(self.seen)
