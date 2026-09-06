"""Deterministic plain-language summaries for the local NPA demonstration."""

from npa_service.application.ports import ChangeSummarizer
from npa_service.domain import ArticleChange, ChangeSummary


class SimulationChangeSummarizer(ChangeSummarizer):
    async def summarize(self, previous_text: str, current_text: str) -> ChangeSummary:
        return ChangeSummary(
            "Срок ответа на обращение стал короче.",
            (
                ArticleChange(
                    "Статья 1",
                    "Срок, за который нужно ответить на обращение, уменьшили.",
                    previous_text,
                    current_text,
                ),
            ),
        )
