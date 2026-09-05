"""`BodyRequirement` — how much text a page needs to count as an article at all."""

from pydantic import BaseModel, Field


class BodyRequirement(BaseModel, frozen=True):
    """Anything shorter is a teaser, a stub or a listing, not a publication."""

    min_words: int = Field(ge=0)

    def accepts(self, word_count: int) -> bool:
        return word_count >= self.min_words
