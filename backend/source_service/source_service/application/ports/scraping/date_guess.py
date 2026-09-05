"""`DateGuess` — the LLM's answer about a page's publication date."""

from pydantic import BaseModel, Field


class DateGuess(BaseModel):
    """The field descriptions double as the model's JSON-schema instructions."""

    is_article: bool = Field(
        description="True only for one individual editorial/publication page, not a listing."
    )
    published_at: str | None = Field(
        default=None,
        description=(
            "Publication date/time of THIS page. Keep timezone if visible. "
            "Null if not reliably identifiable."
        ),
    )
    date_text: str | None = Field(
        default=None,
        description="Exact/near-exact visible date phrase used as evidence, if present.",
    )
    evidence: str | None = Field(
        default=None,
        description=(
            "Short explanation of why this is the page publication date rather than a "
            "date mentioned in the article body."
        ),
    )
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
