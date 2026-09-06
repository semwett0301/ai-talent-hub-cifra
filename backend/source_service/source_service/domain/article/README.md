# domain/article

The article aggregate: one publication on a web source, from a discovered link to
published news. The root holds only the entity; everything it is made of is in `model/`,
everything that judges it is in `rules/`.

- `article.py` — `Article`: the entity. Immutable; each pipeline step returns a copy one
  stage further: `with_content(...)` → `with_publication(...)` → `accept()`, or
  `reject(reason)`. `title` falls back from the page title to the card's link text;
  `identity` is the canonical URL, else the final URL, else the link — the dedupe key.
  `to_news_dto(source)` builds the shared `NewsDTO` — flat: `title`, `text`, the page's
  `description` as `excerpt`, `modified_at` as `updated_at`, `section` as the
  one `source_tags` entry — and refuses anything but an `ACCEPTED` article.
- `model/` — the sub-models: `ArticleContent`, `PublicationDate`, `ArticleStatus`,
  `RejectReason`, `ArticleOrigin`. See `model/README.md`.
- `rules/` — the rules: `ARTICLE_SCORER` (how article-like a link is), `FreshnessWindow`
  (which dates count as news), `BodyRequirement` (how much text makes an article),
  `merge_duplicates` (one story, one record). See `rules/README.md`.

Notes: `accept()` is the only guard — an `ACCEPTED` article always has content, a date
and a title, so consumers need no `None` checks after it. Scores are computed on demand
via `ARTICLE_SCORER`, never stored on the entity; thresholds belong to the use case.
