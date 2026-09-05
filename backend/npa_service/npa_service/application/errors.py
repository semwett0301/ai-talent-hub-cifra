"""Application errors — raised by use cases / repositories, mapped by the outer layers."""


class NpaAlreadyExistsError(ValueError):
    """An act with this `url` is already stored (the DB unique key refused the insert)."""

    def __init__(self, url: str) -> None:
        super().__init__(f"npa already exists: url={url}")
        self.url = url
