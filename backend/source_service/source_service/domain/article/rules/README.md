# domain/article/rules

Judgements about an article that need nothing but the article itself.

- `scoring.py` — `ARTICLE_RULES` / `ARTICLE_SCORER`: how much a link looks like one
  publication — article path segment (`ARTICLE_PATH_TERMS`, owned here), date in path,
  numeric id, long slug, nesting, headline length, article metadata; a section/junk path
  is a penalty. Reads only what discovery already knows, so a link is scored before its
  page is fetched. Built on the generic `domain.scoring` mechanism and the shared URL
  vocabulary in `domain.scoring.terms`.
- `freshness.py` — `FreshnessWindow(days, timezone)`: `contains(dt)` (fresh, with a
  12-hour future tolerance) and `is_before(dt)` (older than the window). The one rule
  every date check in the crawl goes through.
- `body.py` — `BodyRequirement(min_words)`: `accepts(word_count)` — anything shorter is a
  teaser or a stub, not a publication.
- `ranking.py` — `article_score`, `is_article_like(article, min_score)` (worth fetching?),
  `select_candidates(articles, min_score)` (one per URL, the better-scored sighting wins,
  best first). The rules every discovery route ranks links by.
- `duplicates.py` — `merge_duplicates(articles)`: one story under several addresses is one
  record — collapse by `Article.identity`, the newer publication date wins, newest first.

Notes: thresholds (`candidate_score_threshold`, the hub-link cut-off) are not here —
the rule says how article-like, the use case says how strict.
