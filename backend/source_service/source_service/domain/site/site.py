"""`Site` — the web source being crawled and what belongs to it."""

from pydantic import BaseModel, Field

from source_service.domain.urls import host_matches, normalize_url


class Site(BaseModel, frozen=True):
    """One `WEB` source: its entry URL and the hosts that count as "the same site"."""

    url: str
    name: str | None = None
    enabled: bool = True
    # Extra hosts that belong to this site; empty = the entry host and its subdomains.
    allowed_domains: list[str] = Field(default_factory=list)

    @property
    def seed(self) -> str:
        """The normalised entry URL every crawl starts from."""
        return normalize_url(self.url)

    @property
    def label(self) -> str:
        return self.name or self.seed

    def owns(self, url: str) -> bool:
        """Does this link stay on the site (same host or a subdomain of an allowed one)?"""
        return host_matches(url, self.allowed_domains, self.url)
