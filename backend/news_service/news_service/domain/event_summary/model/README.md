# domain/event_summary/model

Ingestion-stage values `EventSummary` is built from and checkpointed with.

- `news_target.py` — `NewsTarget`: a news message with the stable database identity used by
  the LLM summarization stage.
- `prepared_news.py` — `PreparedNews`: a news message whose event summary is ready to persist.
- `stored_news_state.py` — `StoredNewsState`: minimal persistence state used to make batch
  processing idempotent (has this news already been summarized).
