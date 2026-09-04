"""Small framework-independent helpers for the Crawl4AI adapter."""

import re
from collections.abc import AsyncIterable, Iterable

from bs4 import BeautifulSoup


def is_date_probe_page(page_number: int, start_page: int, interval_pages: int) -> bool:
    return page_number >= start_page and (page_number - start_page) % interval_pages == 0


async def materialize_results(value: object) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, AsyncIterable) or hasattr(value, "__aiter__"):
        return [item async for item in value]  # type: ignore[union-attr]
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict)):
        return list(value)
    return [value]


def selector_score(html: str, selector: str | None) -> tuple[float, int]:
    soup = BeautifulSoup(html or "", "html.parser")
    node = soup.select_one(selector) if selector else soup.body
    if node is None:
        return float("-inf"), 0
    for noise in node.select("nav, footer, aside, form, script, style, [role=navigation]"):
        noise.decompose()
    text = re.sub(r"\s+", " ", node.get_text(" ", strip=True))
    words = len(re.findall(r"\b[\w’'-]+\b", text, flags=re.UNICODE))
    links = len(node.find_all("a"))
    paragraphs = len(node.find_all("p"))
    score = min(words, 2500) + paragraphs * 30 - links * 12
    return (score + 80 if selector == "article" else score), words
