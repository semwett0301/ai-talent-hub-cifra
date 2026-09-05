# parse/reading

Parsing tools for the WEB crawl: dates, listing pages, article pages. Text in, structure or
domain objects out — nothing here fetches.

- `dates.py` — `parse_date(text, timezone)`: lenient free-form date parsing (dateutil) with
  Russian month names, `МСК`, day-first for `dd.mm.yyyy`; a naive result gets the site's
  timezone. `None` when unparseable. Also `RU_MONTH_NAMES` — the one spelled-out list of
  Russian month names (genitive case), the single source both `listing_page.py`'s and
  `article_page.py`'s "does this text look like a date" regexes build their alternation from.
- `html_text.py` — `clean_text(tag, limit=None)`: a BeautifulSoup node's visible text with
  runs of whitespace collapsed to one space, optionally cut to length. Shared by every
  other module here that reads a node's text.
- `listing_page.py` — a listing page's HTML: `listing_cards` (the cards as `DISCOVERED`
  `Article`s in document order, with the date printed on the card), `next_listing_page`
  (`rel=next` / "далее"), `listing_llm_snapshot` (bounded evidence for the classifier) and
  `pagination_link` (the option of that snapshot the classifier pointed at).
- `article_page.py` — an article page's HTML: `extract_html_metadata` (title, author,
  section, language, image, canonical, modified from meta / JSON-LD) and the
  publication-date cascade `extract_publication_date_signal` (JSON-LD → OpenGraph → meta →
  `<time>` → visible DOM; never the body text). Owns `DateSource`, the vocabulary of
  extraction techniques stamped into `PublicationDate.source`.
- `article_body.py` — `choose_text_container(html, min_words)` (once per site: `article` /
  `main` / `[role=main]` / document by prose density), `article_body(html, markdown,
  selector, min_words)` and `word_count`.

Notes: modules here import each other directly (`from .dates import parse_date`), not
through the package, to avoid import cycles.
