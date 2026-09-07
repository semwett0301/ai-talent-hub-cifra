# errors

Application failure signals. The package re-exports its public API from `__init__.py`.

- `news_store_error.py` — persistence failure mapped to the shared batch retry path.
- `news_processing_error.py` — summarization, embedding, or dedup batch failure.
- `event_model_error.py` — OpenRouter setup or structured-inference failure.
- `summary_embedding_error.py` — embedding provider failure or unusable vectors (wrong
  dimension, base64, zero vector).
- `npa_gateway_error.py` — unsuccessful NPA service interaction.
- `npa_conflict_error.py` — specialized duplicate-NPA response.
- `ranking_model_error.py` — impact-assessment failure.
