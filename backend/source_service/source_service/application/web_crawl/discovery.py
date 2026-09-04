from __future__ import annotations

import asyncio
import logging

from source_service.application.ports.news_crawler import NewsCrawler

from .fallback_discovery import FallbackDiscovery
from .listing import (
    is_pagination_url,
    listing_identity,
    listing_llm_snapshot,
)
from .listing_candidates import collect_listing_candidates
from .models import ArticleCandidate, DiscoveryTrace, HubCandidate
from .result_utils import internal_links, markdown_raw, title
from .settings import RuntimeSettings, SiteConfig
from .url_utils import article_score, host_matches, hub_score, normalize_url

logger = logging.getLogger(__name__)


class NewsDiscovery:
    def __init__(self, client: NewsCrawler, settings: RuntimeSettings):
        self.client = client
        self.settings = settings
        self._llm_next_pages: dict[str, str | None] = {}
        self._fallback = FallbackDiscovery(client, settings)

    async def run(self, site: SiteConfig) -> tuple[DiscoveryTrace, list[ArticleCandidate]]:
        seed = normalize_url(str(site.url))
        site_name = site.name or seed
        trace = DiscoveryTrace(site=site_name, seed_url=seed)

        # Primary route: discover listing pages from the home page, never more
        # than two links away.  A listing is then traversed in card order, so
        # dates control stopping rather than a relevance-ranked deep crawl.
        listing_hubs = await self._discover_listing_hubs(site, seed, trace)
        if listing_hubs:
            logger.info(
                "[%s] Listing-фаза: подтверждено лент=%d; обхожу карточки по порядку",
                site_name,
                len(listing_hubs),
            )
            candidates, listing_runs = await collect_listing_candidates(
                self.client, self.settings, listing_hubs, self._llm_next_pages
            )
            trace.hubs = listing_hubs
            trace.listing_runs = listing_runs
            trace.candidate_count = len(candidates)
            if candidates:
                logger.info("[%s] Listing-фаза: собрано кандидатов=%d", site_name, len(candidates))
                return trace, candidates
            trace.errors.append(
                "listing discovery found no article candidates; using BestFirst fallback"
            )

        return await self._fallback.run(site, seed, trace)

    def _limit_hubs(self, hubs: list[HubCandidate]) -> list[HubCandidate]:
        cap = self.settings.max_hubs_per_site
        return hubs[:cap] if cap else hubs

    async def _discover_listing_hubs(
        self, site: SiteConfig, seed: str, trace: DiscoveryTrace
    ) -> list[HubCandidate]:
        seen: set[str] = set()
        found: dict[str, HubCandidate] = {}
        max_pages = self.settings.listing_discovery_max_pages
        llm_calls = 0

        def child_links(results: list) -> list[str]:
            links: list[str] = []
            for result in results:
                base = normalize_url(str(getattr(result, "url", "")))
                if not base:
                    continue
                for link in internal_links(result):
                    href = normalize_url(str(link.get("href") or ""), base=base)
                    if (
                        not href
                        or not host_matches(href, site.allowed_domains, seed)
                        or is_pagination_url(href)
                    ):
                        continue
                    label = str(link.get("text") or link.get("title") or "").strip()
                    if article_score(href, title=label, context=label) < 0.35:
                        links.append(href)
            return links

        async def scrape_batch(frontier: list[str], depth: int) -> list:
            batch: list[str] = []
            for url in frontier:
                identity = listing_identity(url)
                if identity in seen:
                    continue
                if max_pages and len(seen) + len(batch) >= max_pages:
                    break
                seen.add(identity)
                batch.append(url)
            if not batch:
                return []
            logger.info(
                "[listing/frontier] depth=%d: скраплю %d кандидатов параллельно (всего найдено=%d)",
                depth,
                len(batch),
                len(seen),
            )
            results = await self.client.crawl_pages(batch)
            logger.info(
                "[listing/frontier] depth=%d: успешно получено=%d/%d",
                depth,
                len(results),
                len(batch),
            )
            return results

        async def classify_batch(results: list, depth: int):
            nonlocal llm_calls
            probes = []
            for result in results:
                result_url = normalize_url(str(getattr(result, "url", "")))
                if not result_url:
                    continue
                html = getattr(result, "html", None) or getattr(result, "cleaned_html", None) or ""
                probes.append((result_url, depth, result, html))
            limit = self.settings.listing_llm_max_calls_per_site
            if limit:
                probes = probes[: max(0, limit - llm_calls)]
            llm_calls += len(probes)
            logger.info(
                "[listing/llm] depth=%d: запросов=%d; async-волна до %d одновременно",
                depth,
                len(probes),
                self.settings.listing_llm_concurrency,
            )
            gate = asyncio.Semaphore(self.settings.listing_llm_concurrency)

            async def classify(probe):
                result_url, probe_depth, result, html = probe
                snapshot = listing_llm_snapshot(html, base_url=result_url)
                async with gate:
                    decision = await self.client.classify_listing(url=result_url, snapshot=snapshot)
                return result_url, probe_depth, result, snapshot, decision

            return await asyncio.gather(*(classify(probe) for probe in probes))

        def register(classified) -> list:
            accepted = []
            for result_url, depth, result, snapshot, decision in classified:
                trace.listing_classifications.append(
                    {
                        "url": result_url,
                        "depth": depth,
                        "is_listing": decision.is_listing if decision else None,
                        "may_contain_news_listings": decision.may_contain_news_listings
                        if decision
                        else None,
                        "confidence": decision.confidence if decision else None,
                        "rationale": decision.rationale if decision else "llm_failed",
                    }
                )
                if (
                    not decision
                    or not decision.is_listing
                    or decision.confidence < self.settings.listing_llm_min_confidence
                ):
                    continue
                if decision.next_page_index is not None:
                    pages = snapshot.get("pagination", [])
                    if decision.next_page_index < len(pages):
                        self._llm_next_pages[result_url] = str(
                            pages[decision.next_page_index]["url"]
                        )
                item = HubCandidate(
                    url=result_url,
                    score=hub_score(result_url, title(result), markdown_raw(result)),
                    title=title(result) or None,
                    source="adaptive",
                )
                found[listing_identity(result_url)] = item
                accepted.append((result_url, depth, result, snapshot, decision))
                logger.info(
                    "[listing/llm] ACCEPT depth=%d confidence=%.2f url=%s reason=%s",
                    depth,
                    decision.confidence,
                    result_url,
                    decision.rationale,
                )
            return accepted

        root = await scrape_batch([seed], 0)
        if self.settings.listing_discovery_max_depth == 0:
            register(await classify_batch(root, 0))
        else:
            first = await scrape_batch(child_links(root), 1)
            first_classified = await classify_batch(first, 1)
            first_listings = register(first_classified)
            expand = [
                result
                for _, _, result, _, decision in first_classified
                if decision is None
                or (not decision.is_listing and decision.may_contain_news_listings)
            ]
            logger.info(
                "[listing/branch] depth=1: listing=%d expand=%d pruned=%d",
                len(first_listings),
                len(expand),
                len(first) - len(first_listings) - len(expand),
            )
            if self.settings.listing_discovery_max_depth >= 2 and expand:
                second = await scrape_batch(child_links(expand), 2)
                register(await classify_batch(second, 2))
        logger.info("[listing/llm] итог: подтверждено listing=%d", len(found))
        # A homepage can itself be the only listing (common for small sites).
        if not found:
            found[listing_identity(seed)] = HubCandidate(
                url=seed, score=0.10, title=site.name, source="seed"
            )
        return self._limit_hubs(sorted(found.values(), key=lambda item: item.score, reverse=True))
