"""Normalise crawler result fields without depending on Crawl4AI classes."""


def markdown_raw(result) -> str:
    markdown = getattr(result, "markdown", None)
    if isinstance(markdown, str):
        return markdown
    return str(getattr(markdown, "raw_markdown", None) or "")


def markdown_fit(result) -> str:
    markdown = getattr(result, "markdown", None)
    if isinstance(markdown, str):
        return markdown
    return str(
        getattr(markdown, "fit_markdown", None) or getattr(markdown, "raw_markdown", None) or ""
    )


def metadata(result) -> dict:
    value = getattr(result, "metadata", None)
    return dict(value) if isinstance(value, dict) else {}


def title(result) -> str:
    values = metadata(result)
    return str(values.get("title") or values.get("og:title") or "").strip()


def internal_links(result) -> list[dict]:
    value = getattr(result, "links", None)
    if isinstance(value, dict):
        return value.get("internal", []) or []
    return []
