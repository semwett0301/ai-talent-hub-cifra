from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .browser_fallback import browser_use_find_hubs
from .config import EnvSettings
from .crawl_client import Crawl4AIClient
from .discovery import NewsDiscovery
from .extractor import ArticleExtractor
from .models import AppConfig, ArticleCandidate, ArticleRecord, HubCandidate
from .url_utils import article_score, host_matches, normalize_url

logger = logging.getLogger(__name__)


class NewsPipeline:
    def __init__(self, config: AppConfig, env: EnvSettings):
        self.config = config
        self.env = env
        self.discovery_traces = []

    async def run(self, only_site: str | None = None) -> list[ArticleRecord]:
        settings = self.config.settings
        selected = [s for s in self.config.sites if s.enabled and (only_site is None or (s.name or "") == only_site)]
        all_articles: dict[str, ArticleRecord] = {}

        async with Crawl4AIClient(settings, self.env) as client:
            discovery = NewsDiscovery(client, settings)
            extractor = ArticleExtractor(client, settings)

            for site in selected:
                site_name = site.name or str(site.url)
                logger.info("[%s] Этап 1/3: ищу listing-страницы от главной (глубина ≤ 2)", site_name)
                trace, candidates = await discovery.run(site)

                if (
                    settings.browser_use_fallback
                    and len(candidates) < settings.browser_fallback_trigger_candidates_below
                ):
                    trace.browser_fallback_used = True
                    hubs = await browser_use_find_hubs(site, settings, self.env)
                    if hubs:
                        merged_hubs = self._merge_hubs(trace.hubs, hubs)
                        trace.hubs = merged_hubs[: settings.max_hubs_per_site] if settings.max_hubs_per_site else merged_hubs
                        extra = await self._crawl_browser_hubs(client, site, hubs)
                        merged_candidates = self._merge_candidates(candidates, extra)
                        candidates = merged_candidates[: settings.max_article_candidates_per_site] if settings.max_article_candidates_per_site else merged_candidates
                        trace.candidate_count = len(candidates)

                self.discovery_traces.append(trace)
                logger.info(
                    "[%s] Этап 1/3 завершён: listing=%d, кандидатов статей=%d, adaptive_confidence=%s",
                    site_name,
                    len(trace.hubs),
                    len(candidates),
                    f"{trace.adaptive_confidence:.2f}" if trace.adaptive_confidence is not None else "n/a",
                )

                if candidates:
                    logger.info("[%s] Этап 2/3: подбираю стратегию очистки текста по первой статье", site_name)
                    trace.article_text_strategy = await client.calibrate_article_text(candidates[0].url)
                logger.info("[%s] Этап 3/3: извлекаю статьи и проверяю даты", site_name)
                extracted = await extractor.extract_many(candidates, site_name)
                trace.extraction = extractor.last_run_stats
                for article in extracted:
                    key = article.canonical_url or article.url
                    old = all_articles.get(key)
                    if old is None or article.published_at > old.published_at:
                        all_articles[key] = article
                logger.info("[%s] Готово: свежих статей=%d; статистика=%s", site_name, len(extracted), trace.extraction)

        return sorted(all_articles.values(), key=lambda a: a.published_at, reverse=True)

    async def _crawl_browser_hubs(self, client: Crawl4AIClient, site, hubs: list[HubCandidate]) -> list[ArticleCandidate]:
        out: list[ArticleCandidate] = []
        seed = normalize_url(str(site.url))
        for hub in hubs:
            try:
                results, _ = await client.best_first_discover(hub.url)
            except Exception:
                logger.exception("Browser fallback hub crawl failed: %s", hub.url)
                continue
            for result in results:
                url = normalize_url(str(getattr(result, "url", "")))
                if not url or not host_matches(url, site.allowed_domains, seed):
                    continue
                md = getattr(result, "metadata", None) or {}
                title = str(md.get("title") or "") if isinstance(md, dict) else ""
                score = article_score(url, title=title, metadata=md if isinstance(md, dict) else {})
                if score >= self.config.settings.candidate_score_threshold:
                    out.append(ArticleCandidate(url=url, source_hub=hub.url, title_hint=title or None, score=score, origin="browser_use"))
        return out

    @staticmethod
    def _merge_hubs(a, b):
        out = {x.url: x for x in a}
        for x in b:
            if x.url not in out or x.score > out[x.url].score:
                out[x.url] = x
        return sorted(out.values(), key=lambda x: x.score, reverse=True)

    @staticmethod
    def _merge_candidates(a, b):
        out = {x.url: x for x in a}
        for x in b:
            if x.url not in out or x.score > out[x.url].score:
                out[x.url] = x
        return sorted(out.values(), key=lambda x: x.score, reverse=True)

    def save(self, articles: list[ArticleRecord]) -> tuple[Path, Path, Path]:
        out_dir = Path(self.config.settings.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(ZoneInfo(self.config.settings.timezone)).strftime("%Y%m%d_%H%M%S")
        jsonl_path = out_dir / f"news_{stamp}.jsonl"
        json_path = out_dir / f"news_{stamp}.json"
        trace_path = out_dir / f"discovery_{stamp}.json"

        with jsonl_path.open("w", encoding="utf-8") as f:
            for article in articles:
                f.write(article.model_dump_json() + "\n")
        json_path.write_text(
            json.dumps([a.model_dump(mode="json") for a in articles], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        trace_path.write_text(
            json.dumps([t.model_dump(mode="json") for t in self.discovery_traces], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return jsonl_path, json_path, trace_path
