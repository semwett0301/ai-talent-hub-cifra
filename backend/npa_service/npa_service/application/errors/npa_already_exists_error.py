"""Duplicate tracked URL error."""


class NpaAlreadyExistsError(ValueError):
    def __init__(self, url: str) -> None:
        super().__init__(f"npa already exists: url={url}")
        self.url = url
