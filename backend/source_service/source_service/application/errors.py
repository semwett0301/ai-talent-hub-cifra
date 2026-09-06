"""Application errors — raised by use cases / repositories, mapped by the outer layers."""


class SourceAlreadyExistsError(ValueError):
    """A source with this address is already registered (the DB unique key refused it)."""

    def __init__(self, link: str) -> None:
        super().__init__(f"source already exists: link={link}")
        self.link = link


class SourceNotRelevantError(ValueError):
    """A source the crawler found no news on cannot be enabled."""

    def __init__(self, link: str) -> None:
        super().__init__(f"source is not a news resource: link={link}")
        self.link = link
