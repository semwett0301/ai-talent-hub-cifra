# services/news_feed

The read side of stored news. Unrelated to the ingestion pipeline — its own
subpackage, not a pipeline stage.

- `news_feed.py` — `NewsFeed`: over `NewsRepository` — `list(query)` (items matching the
  filters, one per event cluster so the feed never repeats a story, and only clusters the
  ranker judged relevant — low-relevance and not-yet-ranked items never reach the reader,
  except on the alerts tab, which shows every `is_alert` item — newest publication
  first), `get`, `dismiss` / `restore` (stage
  `dismissed_at` set / cleared, then `commit()`; None and no commit for an unknown id,
  which the API maps to 404).
