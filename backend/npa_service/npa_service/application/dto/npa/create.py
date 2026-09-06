"""Input contract for adding a State Duma bill to tracking."""

from pydantic import BaseModel, HttpUrl


class NpaCreate(BaseModel):
    url: HttpUrl
