"""`clean_text` — a BeautifulSoup node's visible text, whitespace collapsed to one space."""

import re
from typing import Any

_WHITESPACE_RE = re.compile(r"\s+")


def clean_text(tag: Any, limit: int | None = None) -> str:
    text = _WHITESPACE_RE.sub(" ", tag.get_text(" ", strip=True))
    return text[:limit] if limit is not None else text
