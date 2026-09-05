"""`ArticleJudgement` — DATED → ACCEPTED | REJECTED(OUT_OF_WINDOW | NO_TITLE). No I/O."""

from common.core.logging import get_logger
from common.core.settings import WebCrawlSettings

from source_service.domain import Article, ArticleStatus, FreshnessWindow, RejectReason

logger = get_logger(__name__)


class ArticleJudgement:
    """The last word on a dated article: fresh enough, and titled."""

    def __init__(self, settings: WebCrawlSettings) -> None:
        self.__window = FreshnessWindow(days=settings.days, timezone=settings.timezone)

    def run(self, articles: list[Article]) -> list[Article]:
        """Every article back, the `DATED` ones judged; anything else passes through."""
        dated = [a for a in articles if a.status is ArticleStatus.DATED]
        rest = [a for a in articles if a.status is not ArticleStatus.DATED]

        judged = [self.__judge(article) for article in dated]
        logger.debug(
            "articles judged: dated=%d accepted=%d",
            len(judged),
            sum(1 for a in judged if a.status is ArticleStatus.ACCEPTED),
        )
        return rest + judged

    def __judge(self, article: Article) -> Article:
        if article.status is not ArticleStatus.DATED or article.publication is None:
            raise ValueError(
                f"judgement expects a DATED article, got {article.status}: {article.url}"
            )

        if not self.__window.contains(article.publication.value):
            return article.reject(RejectReason.OUT_OF_WINDOW)
        if not article.title:
            return article.reject(RejectReason.NO_TITLE)
        return article.accept()
