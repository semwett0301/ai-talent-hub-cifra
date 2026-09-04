"""Adaptive and best-first fallback for sites without usable listings."""

import logging

from source_service.application.ports import NewsCrawler

from .models import ArticleCandidate, DiscoveryTrace, HubCandidate
from .result_utils import internal_links, markdown_raw, metadata, title
from .settings import RuntimeSettings, SiteConfig
from .url_utils import article_score, host_matches, hub_score, normalize_url

logger = logging.getLogger(__name__)


class FallbackDiscovery:
    def __init__(self, client: NewsCrawler, settings: RuntimeSettings) -> None:
        self.client = client
        self.settings = settings

    async def run(self, site: SiteConfig, seed: str, trace: DiscoveryTrace):
        adaptive = await self._adaptive(seed, trace)
        hubs = self._select_hubs(site, seed, adaptive, "adaptive")
        if not hubs:
            hubs = [HubCandidate(url=seed, score=0.10, title=site.name or seed, source="seed")]
        best: dict[str, list] = {}
        runs: list[dict] = []
        if self.settings.best_first_fallback:
            for hub in self._limit(hubs):
                try:
                    results, stats = await self.client.best_first_discover(hub.url)
                    best[hub.url] = results
                    runs.append({"hub_url": hub.url, **stats})
                except Exception as exc:
                    logger.exception("Best-first discovery failed for %s", hub.url)
                    trace.errors.append(f"best_first {hub.url}: {exc}")
        flat_best = [item for results in best.values() for item in results]
        hubs = self._limit(
            self._merge(hubs + self._select_hubs(site, seed, flat_best, "best_first"))
        )
        trace.hubs, trace.best_first_runs = hubs, runs
        candidates = self._collect(site, seed, adaptive, best, hubs)
        trace.candidate_count = len(candidates)
        return trace, candidates

    async def _adaptive(self, seed: str, trace: DiscoveryTrace) -> list:
        if not self.settings.adaptive_enabled:
            return []
        try:
            state, trace.adaptive_confidence = await self.client.adaptive_discover(seed)
            trace.adaptive_metrics = dict(getattr(state, "metrics", None) or {})
            urls = getattr(state, "crawl_order", None) or getattr(state, "crawled_urls", None) or []
            trace.adaptive_urls = [url for raw in urls if (url := normalize_url(str(raw)))]
            return list(getattr(state, "knowledge_base", None) or [])
        except Exception as exc:
            logger.exception("Adaptive discovery failed for %s", seed)
            trace.errors.append(f"adaptive: {exc}")
            return []

    def _limit(self, hubs: list[HubCandidate]) -> list[HubCandidate]:
        cap = self.settings.max_hubs_per_site
        return hubs[:cap] if cap else hubs

    def _select_hubs(self, site: SiteConfig, seed: str, results: list, source: str):
        found: dict[str, HubCandidate] = {}
        for result in results:
            url = normalize_url(str(getattr(result, "url", "")))
            if not url or not host_matches(url, site.allowed_domains, seed):
                continue
            self._add_hub(found, url, title(result), markdown_raw(result), source)
            for link in internal_links(result):
                href = normalize_url(str(link.get("href") or ""), base=url)
                if href and host_matches(href, site.allowed_domains, seed):
                    label = str(link.get("text") or link.get("title") or "").strip()
                    self._add_hub(found, href, label, "", source)
        return sorted(found.values(), key=lambda item: item.score, reverse=True)

    def _add_hub(self, found, url: str, label: str, text: str, source: str) -> None:
        score = hub_score(url, label, text)
        candidate = HubCandidate(url=url, score=score, title=label or None, source=source)
        previous = found.get(url)
        if score >= self.settings.min_hub_score and (previous is None or score > previous.score):
            found[url] = candidate

    @staticmethod
    def _merge(items: list[HubCandidate]) -> list[HubCandidate]:
        found: dict[str, HubCandidate] = {}
        for item in items:
            previous = found.get(item.url)
            if previous is None or item.score > previous.score:
                found[item.url] = item
        return sorted(found.values(), key=lambda item: item.score, reverse=True)

    def _collect(self, site, seed, adaptive, best, hubs) -> list[ArticleCandidate]:
        found: dict[str, ArticleCandidate] = {}
        hub_urls = {hub.url for hub in hubs}

        def add(raw_url, source_hub, label, context, meta, origin):
            url = normalize_url(raw_url, base=source_hub or seed)
            if not url or url in hub_urls or not host_matches(url, site.allowed_domains, seed):
                return
            score = article_score(url, title=label, context=context, metadata=meta)
            candidate = ArticleCandidate(
                url=url, source_hub=source_hub, title_hint=label or None, score=score, origin=origin
            )
            previous = found.get(url)
            if score >= self.settings.candidate_score_threshold and (
                previous is None or score > previous.score
            ):
                found[url] = candidate

        def collect(results, source_hub, origin):
            for result in results:
                page_url = normalize_url(str(getattr(result, "url", "")))
                if page_url:
                    add(page_url, source_hub, title(result), "", metadata(result), origin)
                for link in internal_links(result):
                    label = str(link.get("title") or link.get("text") or "").strip()
                    add(
                        str(link.get("href") or ""),
                        source_hub or page_url,
                        label,
                        label,
                        {},
                        "link",
                    )

        collect(adaptive, None, "adaptive")
        for hub_url, results in best.items():
            collect(results, hub_url, "best_first")
        items = sorted(found.values(), key=lambda item: item.score, reverse=True)
        cap = self.settings.max_article_candidates_per_site
        return items[:cap] if cap else items
