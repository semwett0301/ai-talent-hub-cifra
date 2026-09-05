"""Article body text: pick the page's text container once per site, then cut the body."""

import re

from bs4 import BeautifulSoup

from .html_text import clean_text

WORD_RE = re.compile(r"\b[\w’'-]+\b", re.UNICODE)
BLANK_LINES_RE = re.compile(r"\n{3,}")
NOISE_SELECTOR = "nav, footer, aside, form, script, style, [role=navigation]"
# Tried in this order on one sample article; `None` = the whole document (fit markdown).
CONTAINER_CANDIDATES: tuple[str | None, ...] = ("article", "main", "[role='main']", None)
WORDS_CAP = 2500
PARAGRAPH_WEIGHT = 30
LINK_PENALTY = 12
ARTICLE_TAG_BONUS = 80


def word_count(text: str) -> int:
    return len(WORD_RE.findall(text or ""))


def choose_text_container(html: str, min_words: int) -> str | None:
    """The CSS selector with the highest prose density on a sample article, or `None`
    when no candidate holds a real body — then the document-level markdown is safer."""
    ranked = [(_container_score(html, selector), selector) for selector in CONTAINER_CANDIDATES]
    (_, words), selector = max(ranked, key=lambda item: item[0][0])
    return selector if words >= min_words else None


def article_body(html: str, markdown: str, selector: str | None, min_words: int) -> str:
    """Text of the calibrated container without navigation; the pruned markdown when the
    container is missing or too thin on this page."""
    if selector and html:
        node = BeautifulSoup(html, "html.parser").select_one(selector)
        if node is not None:
            for noise in node.select(NOISE_SELECTOR):
                noise.decompose()
            text = BLANK_LINES_RE.sub("\n\n", node.get_text("\n", strip=True)).strip()
            if word_count(text) >= min_words:
                return text
    return BLANK_LINES_RE.sub("\n\n", markdown or "").strip()


def _container_score(html: str, selector: str | None) -> tuple[float, int]:
    soup = BeautifulSoup(html or "", "html.parser")
    node = soup.select_one(selector) if selector else soup.body
    if node is None:
        return float("-inf"), 0

    for noise in node.select(NOISE_SELECTOR):
        noise.decompose()
    text = clean_text(node)
    words = word_count(text)
    score = min(words, WORDS_CAP) + PARAGRAPH_WEIGHT * len(node.find_all("p"))
    score -= LINK_PENALTY * len(node.find_all("a"))
    return (score + ARTICLE_TAG_BONUS if selector == "article" else score), words
