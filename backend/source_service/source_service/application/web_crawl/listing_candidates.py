"""Chronological article collection from confirmed listing pages."""

import logging

from source_service.application.ports import NewsCrawler

from .date_utils import is_older_than_window
from .listing import listing_identity, listing_links, next_listing_page
from .models import ArticleCandidate, HubCandidate
from .settings import RuntimeSettings
from .url_utils import article_score

logger = logging.getLogger(__name__)


async def collect_listing_candidates(
    client: NewsCrawler,
    settings: RuntimeSettings,
    hubs: list[HubCandidate],
    llm_next_pages: dict[str, str | None],
) -> tuple[list[ArticleCandidate], list[dict]]:
    found: dict[str, ArticleCandidate] = {}
    listing_ids = {listing_identity(hub.url) for hub in hubs}
    runs: list[dict] = []
    for hub in hubs:
        url: str | None = hub.url
        seen_pages: set[str] = set()
        pages = 0
        stopped_on_old = False
        cap = settings.listing_max_pages_per_hub
        while url and url not in seen_pages and (not cap or pages < cap):
            seen_pages.add(url)
            pages += 1
            try:
                result = await client.crawl_page(url)
            except Exception:
                logger.exception("Listing crawl failed: %s", url)
                break
            if result is None:
                break
            html = getattr(result, "html", None) or getattr(result, "cleaned_html", None) or ""
            links = listing_links(
                html,
                base_url=url,
                timezone=settings.timezone,
                score_threshold=settings.candidate_score_threshold,
            )
            before = len(found)
            for link in links:
                if listing_identity(link.url) in listing_ids:
                    continue
                if link.published_at and is_older_than_window(
                    link.published_at, settings.days, settings.timezone
                ):
                    stopped_on_old = True
                    break
                found.setdefault(
                    link.url,
                    ArticleCandidate(
                        url=link.url,
                        source_hub=hub.url,
                        title_hint=link.title,
                        score=article_score(link.url, title=link.title, context=link.title),
                        origin="listing",
                    ),
                )
            logger.info(
                "[listing/cards] hub=%s page=%d cards=%d new=%d",
                hub.url,
                pages,
                len(links),
                len(found) - before,
            )
            if stopped_on_old:
                break
            url = llm_next_pages.get(url) or next_listing_page(html, base_url=url)
        runs.append(
            {"hub_url": hub.url, "pages_crawled": pages, "stopped_on_old_card": stopped_on_old}
        )
    candidates = list(found.values())
    cap = settings.max_article_candidates_per_site
    return (candidates[:cap] if cap else candidates), runs
