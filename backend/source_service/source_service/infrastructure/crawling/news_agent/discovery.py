from __future__ import annotations

import asyncio
import logging

from .crawl_client import Crawl4AIClient, markdown_raw
from .date_utils import is_older_than_window
from .listing import (
    is_pagination_url,
    listing_identity,
    listing_links,
    listing_llm_snapshot,
    next_listing_page,
)
from .models import ArticleCandidate, DiscoveryTrace, HubCandidate, RuntimeSettings, SiteConfig
from .url_utils import article_score, host_matches, hub_score, normalize_url

logger = logging.getLogger(__name__)


def _metadata(result) -> dict:
    value = getattr(result, "metadata", None)
    return dict(value) if isinstance(value, dict) else {}


def _title(result) -> str:
    md = _metadata(result)
    return str(md.get("title") or md.get("og:title") or "").strip()


def _internal_links(result) -> list[dict]:
    value = getattr(result, "links", None)
    if isinstance(value, dict):
        return value.get("internal", []) or []
    return []


class NewsDiscovery:
    def __init__(self, client: Crawl4AIClient, settings: RuntimeSettings):
        self.client = client
        self.settings = settings
        self._llm_next_pages: dict[str, str | None] = {}

    async def run(self, site: SiteConfig) -> tuple[DiscoveryTrace, list[ArticleCandidate]]:
        seed = normalize_url(str(site.url))
        site_name = site.name or seed
        trace = DiscoveryTrace(site=site_name, seed_url=seed)

        # Primary route: discover listing pages from the home page, never more
        # than two links away.  A listing is then traversed in card order, so
        # dates control stopping rather than a relevance-ranked deep crawl.
        listing_hubs = await self._discover_listing_hubs(site, seed, trace)
        if listing_hubs:
            logger.info("[%s] Listing-фаза: подтверждено лент=%d; обхожу карточки по порядку", site_name, len(listing_hubs))
            candidates, listing_runs = await self._collect_listing_candidates(site, seed, listing_hubs)
            trace.hubs = listing_hubs
            trace.listing_runs = listing_runs
            trace.candidate_count = len(candidates)
            if candidates:
                logger.info("[%s] Listing-фаза: собрано кандидатов=%d", site_name, len(candidates))
                return trace, candidates
            trace.errors.append("listing discovery found no article candidates; using BestFirst fallback")

        adaptive_results: list = []
        if self.settings.adaptive_enabled:
            try:
                state, confidence = await self.client.adaptive_discover(seed)
                adaptive_results = list(getattr(state, "knowledge_base", None) or [])
                trace.adaptive_confidence = confidence
                trace.adaptive_metrics = dict(getattr(state, "metrics", None) or {})
                trace.adaptive_urls = [
                    normalize_url(str(u)) for u in (getattr(state, "crawl_order", None) or getattr(state, "crawled_urls", None) or [])
                    if normalize_url(str(u))
                ]
            except Exception as exc:
                logger.exception("Adaptive discovery failed for %s", seed)
                trace.errors.append(f"adaptive: {exc}")

        hubs = self._select_hubs(site, seed, adaptive_results, source="adaptive")
        # The seed is always a safe fallback entry point, but deliberately low scored.
        if not hubs:
            hubs = [HubCandidate(url=seed, score=0.10, title=site_name, source="seed")]

        best_first_results: dict[str, list] = {}
        best_first_runs: list[dict] = []
        if self.settings.best_first_fallback:
            # Deep-crawl the strongest hubs. If adaptive returned only a weak seed, this
            # naturally becomes a general site crawl.
            for hub in self._limit_hubs(hubs):
                try:
                    results, run_stats = await self.client.best_first_discover(hub.url)
                    best_first_results[hub.url] = results
                    best_first_runs.append({"hub_url": hub.url, **run_stats})
                except Exception as exc:
                    logger.exception("Best-first discovery failed for %s", hub.url)
                    trace.errors.append(f"best_first {hub.url}: {exc}")

        # Best-first pages may reveal better/more specific listing hubs than adaptive.
        flat_best = [r for values in best_first_results.values() for r in values]
        extra_hubs = self._select_hubs(site, seed, flat_best, source="best_first")
        hubs = self._limit_hubs(self._merge_hubs(hubs + extra_hubs))
        trace.hubs = hubs
        trace.best_first_runs = best_first_runs

        candidates = self._collect_candidates(site, seed, adaptive_results, best_first_results, hubs)
        trace.candidate_count = len(candidates)
        return trace, candidates

    def _limit_hubs(self, hubs: list[HubCandidate]) -> list[HubCandidate]:
        cap = self.settings.max_hubs_per_site
        return hubs[:cap] if cap else hubs

    async def _discover_listing_hubs(self, site: SiteConfig, seed: str, trace: DiscoveryTrace) -> list[HubCandidate]:
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
                for link in _internal_links(result):
                    href = normalize_url(str(link.get("href") or ""), base=base)
                    if not href or not host_matches(href, site.allowed_domains, seed) or is_pagination_url(href):
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
                depth, len(batch), len(seen),
            )
            results = await self.client.crawl_pages(batch)
            logger.info("[listing/frontier] depth=%d: успешно получено=%d/%d", depth, len(results), len(batch))
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
            logger.info("[listing/llm] depth=%d: запросов=%d; async-волна до %d одновременно", depth, len(probes), self.settings.listing_llm_concurrency)
            gate = asyncio.Semaphore(self.settings.listing_llm_concurrency)
            async def classify(probe):
                result_url, probe_depth, result, html = probe
                snapshot = listing_llm_snapshot(html, base_url=result_url)
                async with gate:
                    decision = await self.client.llm_classify_listing_page(url=result_url, snapshot=snapshot)
                return result_url, probe_depth, result, snapshot, decision
            return await asyncio.gather(*(classify(probe) for probe in probes))

        def register(classified) -> list:
            accepted = []
            for result_url, depth, result, snapshot, decision in classified:
                trace.listing_classifications.append({
                    "url": result_url,
                    "depth": depth,
                    "is_listing": decision.is_listing if decision else None,
                    "may_contain_news_listings": decision.may_contain_news_listings if decision else None,
                    "confidence": decision.confidence if decision else None,
                    "rationale": decision.rationale if decision else "llm_failed",
                })
                if not decision or not decision.is_listing or decision.confidence < self.settings.listing_llm_min_confidence:
                    continue
                if decision.next_page_index is not None:
                    pages = snapshot.get("pagination", [])
                    if decision.next_page_index < len(pages):
                        self._llm_next_pages[result_url] = str(pages[decision.next_page_index]["url"])
                item = HubCandidate(
                    url=result_url,
                    score=hub_score(result_url, _title(result), markdown_raw(result)),
                    title=_title(result) or None,
                    source="adaptive",
                )
                found[listing_identity(result_url)] = item
                accepted.append((result_url, depth, result, snapshot, decision))
                logger.info(
                    "[listing/llm] ACCEPT depth=%d confidence=%.2f url=%s reason=%s",
                    depth, decision.confidence, result_url, decision.rationale,
                )
            return accepted

        root = await scrape_batch([seed], 0)
        if self.settings.listing_discovery_max_depth == 0:
            register(await classify_batch(root, 0))
        else:
            first = await scrape_batch(child_links(root), 1)
            first_classified = await classify_batch(first, 1)
            first_listings = register(first_classified)
            expand = [result for _, _, result, _, decision in first_classified if decision is None or (not decision.is_listing and decision.may_contain_news_listings)]
            logger.info("[listing/branch] depth=1: listing=%d expand=%d pruned=%d", len(first_listings), len(expand), len(first) - len(first_listings) - len(expand))
            if self.settings.listing_discovery_max_depth >= 2 and expand:
                second = await scrape_batch(child_links(expand), 2)
                register(await classify_batch(second, 2))
        logger.info("[listing/llm] итог: подтверждено listing=%d", len(found))
        # A homepage can itself be the only listing (common for small sites).
        if not found:
            found[listing_identity(seed)] = HubCandidate(url=seed, score=0.10, title=site.name, source="seed")
        return self._limit_hubs(sorted(found.values(), key=lambda item: item.score, reverse=True))

    async def _collect_listing_candidates(
        self, site: SiteConfig, seed: str, hubs: list[HubCandidate]
    ) -> tuple[list[ArticleCandidate], list[dict]]:
        dedup: dict[str, ArticleCandidate] = {}
        # A confirmed listing is discovery infrastructure, never an article.
        # Compare pagination-free identities so /news and /news?page=1 are
        # equally protected from entering ArticleCandidate.
        listing_ids = {listing_identity(hub.url) for hub in hubs}
        runs: list[dict] = []
        for hub in hubs:
            url = hub.url
            seen_pages: set[str] = set()
            pages = 0
            stopped_on_old = False
            cap = self.settings.listing_max_pages_per_hub
            logger.info("[listing/cards] старт ленты url=%s", hub.url)
            while url and url not in seen_pages and (not cap or pages < cap):
                seen_pages.add(url)
                pages += 1
                try:
                    result = await self.client.crawl_page(url)
                except Exception:
                    logger.exception("Listing crawl failed: %s", url)
                    break
                if result is None:
                    break
                html = getattr(result, "html", None) or getattr(result, "cleaned_html", None) or ""
                ordered = listing_links(
                    html, base_url=url, timezone=self.settings.timezone,
                    score_threshold=self.settings.candidate_score_threshold,
                )
                before = len(dedup)
                for link in ordered:
                    if listing_identity(link.url) in listing_ids:
                        logger.debug("[listing/cards] пропускаю listing как article candidate: %s", link.url)
                        continue
                    if link.published_at is not None and is_older_than_window(
                        link.published_at, self.settings.days, self.settings.timezone
                    ):
                        stopped_on_old = True
                        logger.info(
                            "[listing/cards] STOP: лента=%s страница=%d; первая старая карточка=%s (%s)",
                            hub.url, pages, link.url, link.published_at.isoformat(),
                        )
                        break
                    candidate = ArticleCandidate(
                        url=link.url, source_hub=hub.url, title_hint=link.title,
                        score=article_score(link.url, title=link.title, context=link.title), origin="listing",
                    )
                    dedup.setdefault(link.url, candidate)
                logger.info(
                    "[listing/cards] лента=%s страница=%d карточек=%d новых_кандидатов=%d",
                    hub.url, pages, len(ordered), len(dedup) - before,
                )
                if stopped_on_old:
                    break
                url = self._llm_next_pages.get(url) or next_listing_page(html, base_url=url)
            runs.append({"hub_url": hub.url, "pages_crawled": pages, "stopped_on_old_card": stopped_on_old})
            logger.info("[listing/cards] завершена лента=%s страниц=%d stop_on_old=%s", hub.url, pages, stopped_on_old)
        candidates = list(dedup.values())
        cap = self.settings.max_article_candidates_per_site
        return (candidates[:cap] if cap else candidates), runs

    def _select_hubs(self, site: SiteConfig, seed: str, results: list, source: str) -> list[HubCandidate]:
        out: dict[str, HubCandidate] = {}
        for result in results:
            url = normalize_url(str(getattr(result, "url", "")))
            if not url or not host_matches(url, site.allowed_domains, seed):
                continue
            score = hub_score(url, _title(result), markdown_raw(result))
            if score < self.settings.min_hub_score:
                continue
            item = HubCandidate(url=url, score=score, title=_title(result) or None, source=source)
            old = out.get(url)
            if old is None or item.score > old.score:
                out[url] = item

            # Important: adaptive result links can point to a listing page not yet crawled.
            for link in _internal_links(result):
                href = normalize_url(str(link.get("href") or ""), base=url)
                if not href or not host_matches(href, site.allowed_domains, seed):
                    continue
                label = str(link.get("text") or link.get("title") or "").strip()
                link_score = hub_score(href, label)
                if link_score >= self.settings.min_hub_score:
                    candidate = HubCandidate(url=href, score=link_score, title=label or None, source=source)
                    old = out.get(href)
                    if old is None or candidate.score > old.score:
                        out[href] = candidate
        return sorted(out.values(), key=lambda x: x.score, reverse=True)

    @staticmethod
    def _merge_hubs(items: list[HubCandidate]) -> list[HubCandidate]:
        out: dict[str, HubCandidate] = {}
        for item in items:
            old = out.get(item.url)
            if old is None or item.score > old.score:
                out[item.url] = item
        return sorted(out.values(), key=lambda x: x.score, reverse=True)

    def _collect_candidates(
        self,
        site: SiteConfig,
        seed: str,
        adaptive_results: list,
        best_first_results: dict[str, list],
        hubs: list[HubCandidate],
    ) -> list[ArticleCandidate]:
        dedup: dict[str, ArticleCandidate] = {}
        hub_set = {h.url for h in hubs}

        def add(url: str, source_hub: str | None, title: str, context: str, md: dict, origin: str):
            norm = normalize_url(url, base=source_hub or seed)
            if not norm or norm in hub_set or not host_matches(norm, site.allowed_domains, seed):
                return
            score = article_score(norm, title=title, context=context, metadata=md)
            if score < self.settings.candidate_score_threshold:
                return
            item = ArticleCandidate(
                url=norm,
                source_hub=source_hub,
                title_hint=title or None,
                score=score,
                origin=origin,
            )
            old = dedup.get(norm)
            if old is None or item.score > old.score:
                dedup[norm] = item

        # Pages already crawled by AdaptiveCrawler can themselves be article candidates.
        for result in adaptive_results:
            url = normalize_url(str(getattr(result, "url", "")))
            if url:
                add(url, None, _title(result), "", _metadata(result), "adaptive")
            for link in _internal_links(result):
                add(
                    str(link.get("href") or ""),
                    url or seed,
                    str(link.get("title") or link.get("text") or "").strip(),
                    str(link.get("text") or "").strip(),
                    {},
                    "link",
                )

        for hub_url, results in best_first_results.items():
            for result in results:
                page_url = normalize_url(str(getattr(result, "url", "")))
                if page_url:
                    add(page_url, hub_url, _title(result), "", _metadata(result), "best_first")
                for link in _internal_links(result):
                    add(
                        str(link.get("href") or ""),
                        hub_url,
                        str(link.get("title") or link.get("text") or "").strip(),
                        str(link.get("text") or "").strip(),
                        {},
                        "link",
                    )

        # Prefer plausible articles but keep discovery permissive; actual article/body/date
        # validation happens after fetching the page.
        items = sorted(dedup.values(), key=lambda x: x.score, reverse=True)
        cap = self.settings.max_article_candidates_per_site
        return items[:cap] if cap else items
