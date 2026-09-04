from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from .crawl_client import Crawl4AIClient, markdown_fit
from .date_utils import is_recent, parse_date
from .html_meta import extract_html_metadata, extract_publication_date_signal
from .models import ArticleCandidate, ArticleRecord, RuntimeSettings
from .url_utils import normalize_url

logger = logging.getLogger(__name__)


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", text or "", flags=re.UNICODE))


def _crawler_metadata(result) -> dict:
    value = getattr(result, "metadata", None)
    return dict(value) if isinstance(value, dict) else {}


class LLMDateGate:
    """Bound concurrent date calls while preserving a hard per-site budget."""

    def __init__(self, *, max_calls: int, concurrency: int):
        self.remaining = max(0, max_calls)
        self.used = 0
        self.max_active = 0
        self._active = 0
        self._budget_lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max(1, concurrency))

    async def run(self, action):
        async with self._budget_lock:
            if self.remaining <= 0:
                return None, False
            self.remaining -= 1
            self.used += 1
        async with self._semaphore:
            self._active += 1
            self.max_active = max(self.max_active, self._active)
            try:
                return await action(), True
            finally:
                self._active -= 1


class ArticleExtractor:
    def __init__(self, client: Crawl4AIClient, settings: RuntimeSettings):
        self.client = client
        self.settings = settings
        self.last_run_stats: dict[str, int | bool | str | None] = {}

    def _article_body(self, result, html: str) -> str:
        selector = self.client.article_css_selector
        if selector and html:
            soup = BeautifulSoup(html, "html.parser")
            node = soup.select_one(selector)
            if node is not None:
                for noise in node.select("nav, footer, aside, form, script, style, [role=navigation]"):
                    noise.decompose()
                text = re.sub(r"\n{3,}", "\n\n", node.get_text("\n", strip=True)).strip()
                if _word_count(text) >= self.settings.min_article_words:
                    return text
        return re.sub(r"\n{3,}", "\n\n", markdown_fit(result)).strip()

    async def extract_many(
        self,
        candidates: list[ArticleCandidate],
        source_site: str,
    ) -> list[ArticleRecord]:
        if not candidates:
            return []
        by_url = {c.url: c for c in candidates}
        urls = list(by_url)
        llm_gate = LLMDateGate(
            max_calls=self.settings.llm_date_max_calls_per_site,
            concurrency=self.settings.llm_date_concurrency,
        )
        out: list[ArticleRecord] = []
        stats: dict[str, int | bool | str | None] = {
            "candidate_urls": len(urls),
            "fetched_urls": 0,
            "batches_fetched": 0,
            "resolved_recent_dates": 0,
            "resolved_out_of_scope_dates": 0,
            "unknown_date_results": 0,
            "llm_date_calls": 0,
            "llm_date_max_parallel": 0,
            "stopped_early": False,
            "stop_reason": None,
        }
        consecutive_old_batches = 0

        # Candidates are ordered by relevance rather than guaranteed publication
        # time, so never stop on a single old page.  Process full batches and
        # require repeated all-old evidence before cutting off the tail.
        batch_size = max(1, self.settings.article_batch_size)
        for offset in range(0, len(urls), batch_size):
            batch_urls = urls[offset:offset + batch_size]
            batch_number = offset // batch_size + 1
            total_batches = (len(urls) + batch_size - 1) // batch_size
            logger.info(
                "[articles] batch %d/%d: загружаю %d URL (обработано до этого %d/%d)",
                batch_number, total_batches, len(batch_urls), offset, len(urls),
            )
            results = await self.client.crawl_articles(batch_urls)
            stats["fetched_urls"] = int(stats["fetched_urls"] or 0) + len(batch_urls)
            stats["batches_fetched"] = int(stats["batches_fetched"] or 0) + 1
            batch_recent_dates = 0
            batch_old_dates = 0

            work = []
            for result in results:
                result_url = normalize_url(str(getattr(result, "url", "")))
                candidate = by_url.get(result_url)
                if candidate is None:
                    # Redirects may change URL; retain a best-effort candidate shell.
                    candidate = ArticleCandidate(url=result_url or str(getattr(result, "url", "")), score=0.0)
                work.append(self._extract_one(result, candidate, source_site, llm_gate))

            for record, used_llm, date_scope in await asyncio.gather(*work):
                if used_llm:
                    stats["llm_date_calls"] = int(stats["llm_date_calls"] or 0) + 1
                if date_scope == "recent":
                    batch_recent_dates += 1
                    stats["resolved_recent_dates"] = int(stats["resolved_recent_dates"] or 0) + 1
                elif date_scope == "out_of_scope":
                    batch_old_dates += 1
                    stats["resolved_out_of_scope_dates"] = int(stats["resolved_out_of_scope_dates"] or 0) + 1
                else:
                    stats["unknown_date_results"] = int(stats["unknown_date_results"] or 0) + 1
                if record is not None:
                    out.append(record)

            resolved_dates = batch_recent_dates + batch_old_dates
            logger.info(
                "[articles] batch %d/%d: recent=%d old=%d unknown=%d llm_date_calls=%d emitted=%d",
                batch_number, total_batches, batch_recent_dates, batch_old_dates,
                len(results) - resolved_dates, stats["llm_date_calls"], len(out),
            )
            all_resolved_dates_are_old = resolved_dates >= self.settings.out_of_scope_min_resolved_dates_per_batch and batch_recent_dates == 0
            if all_resolved_dates_are_old:
                consecutive_old_batches += 1
            else:
                consecutive_old_batches = 0
            if (
                self.settings.stop_on_out_of_scope_batches
                and consecutive_old_batches >= self.settings.out_of_scope_consecutive_batches
            ):
                stats["stopped_early"] = True
                stats["stop_reason"] = "consecutive_out_of_scope_date_batches"
                logger.info("[articles] STOP: %d подряд batch только со старыми датами", consecutive_old_batches)
                break

        stats["llm_date_max_parallel"] = llm_gate.max_active
        self.last_run_stats = stats
        return out

    async def _extract_one(self, result, candidate: ArticleCandidate, source_site: str, llm_gate: LLMDateGate):
        crawler_meta = _crawler_metadata(result)
        html = getattr(result, "html", None) or getattr(result, "cleaned_html", None) or ""
        body = self._article_body(result, html)
        words = _word_count(body)
        if words < self.settings.min_article_words:
            return None, False, "unknown"
        html_meta = extract_html_metadata(html)
        signal = extract_publication_date_signal(html)

        published_at = parse_date(signal.value, self.settings.timezone) if signal.value else None
        date_source = signal.source
        date_confidence = signal.confidence
        date_evidence = signal.evidence
        used_llm = False

        # Core requirement: if the page does not expose a reliable machine-readable
        # publication date, ask the LLM to understand the visible page semantics.
        if published_at is None and self.settings.llm_date_fallback:
            async def extract_date():
                try:
                    return await self.client.llm_extract_publication_date(candidate.url)
                except Exception:
                    logger.exception("LLM date extraction failed for %s", candidate.url)
                    return None

            guess, used_llm = await llm_gate.run(extract_date)
            if guess is not None:
                if not guess.is_article:
                    return None, used_llm, "unknown"
                if guess.published_at and guess.confidence >= self.settings.llm_date_min_confidence:
                    parsed = parse_date(guess.published_at, self.settings.timezone)
                    if parsed is not None:
                        published_at = parsed
                        date_source = "crawl4ai_llm"
                        date_confidence = guess.confidence
                        date_evidence = guess.date_text or guess.evidence

        if published_at is None:
            if self.settings.require_publication_date:
                return None, used_llm, "unknown"
            # Current model requires a publication date, so permissive mode still cannot emit a record.
            return None, used_llm, "unknown"

        if not is_recent(published_at, self.settings.days, self.settings.timezone):
            return None, used_llm, "out_of_scope"

        title = (
            html_meta.get("title")
            or crawler_meta.get("title")
            or crawler_meta.get("og:title")
            or candidate.title_hint
        )
        if not title:
            return None, used_llm, "recent"

        modified = parse_date(str(html_meta.get("modified_at")), self.settings.timezone) if html_meta.get("modified_at") else None
        final_url = normalize_url(str(getattr(result, "redirected_url", None) or getattr(result, "url", candidate.url))) or candidate.url
        canonical = html_meta.get("canonical_url")
        canonical = normalize_url(str(canonical), base=final_url) if canonical else None

        return ArticleRecord(
            url=final_url,
            canonical_url=canonical,
            source_site=source_site,
            source_hub=candidate.source_hub,
            title=str(title).strip(),
            published_at=published_at,
            modified_at=modified,
            author=str(html_meta.get("author")).strip() if html_meta.get("author") else None,
            section=str(html_meta.get("section")).strip() if html_meta.get("section") else None,
            language=str(html_meta.get("language") or crawler_meta.get("language")).strip() if (html_meta.get("language") or crawler_meta.get("language")) else None,
            description=str(html_meta.get("description") or crawler_meta.get("description")).strip() if (html_meta.get("description") or crawler_meta.get("description")) else None,
            image_url=str(html_meta.get("image_url")).strip() if html_meta.get("image_url") else None,
            text=body,
            word_count=words,
            fetched_at=datetime.now(ZoneInfo(self.settings.timezone)),
            date_source=date_source or "crawl4ai_llm",
            date_confidence=date_confidence,
            date_evidence=date_evidence,
            metadata={
                "candidate_score": candidate.score,
                "candidate_origin": candidate.origin,
                "crawler_metadata": crawler_meta,
                "html_metadata": html_meta,
                "llm_date_fallback_used": used_llm,
            },
        ), used_llm, "recent"
