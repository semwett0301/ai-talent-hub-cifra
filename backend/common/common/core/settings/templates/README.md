# common.core.settings.templates

One settings group per module. A group is a `SettingsTemplate` (a `BaseSettings` bound to
the repo-root `.env`, `extra="ignore"`); it either sets `env_prefix` when all its
variables share one, or names its fields exactly like the variables.

| Module | Class | Variables |
|---|---|---|
| `base.py` | `SettingsTemplate`, `ENV_FILE` | — (the shared config) |
| `app.py` | `AppSettings` | `APP_NAME`, `ENVIRONMENT`, `DEBUG` |
| `postgres.py` | `PostgresSettings` | `POSTGRES_*`, `DATABASE_URL`; computed `async_database_url` / `sync_database_url` |
| `rabbit.py` | `RabbitSettings` | `RABBITMQ_URL`, `NEWS_EXCHANGE` |
| `edge.py` | `EdgeSettings` | `SOURCES_API_PREFIX`, `NEWS_API_PREFIX` (shared with nginx) |
| `sources.py` | `SourceSchedulerSettings` | `SOURCE_POLL_INTERVAL_SECONDS` |
| `news.py` | `NewsConsumerSettings` | `NEWS_QUEUE`, `NEWS_BATCH_SIZE`, `NEWS_BATCH_INTERVAL_SECONDS`, `NEWS_REQUEUE_ON_STORE_ERROR` |
| `news_dedup.py` | `NewsDedupSettings` | `NEWS_DEDUP_*` model, embedding, retrieval, and policy settings |
| `news_ranking.py` | `NewsRankingSettings` | `NEWS_RANKING_*` model, batching, timeout, and document settings |
| `telegram.py` | `TelegramSettings` | `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_SESSION` |
| `web_crawl.py` | `WebCrawlSettings` | `WEB_CRAWL_DAYS`, `WEB_CRAWL_MAX_ARTICLES`, `WEB_CRAWL_LLM_ENABLED` + every tuning knob of the crawl as `WEB_CRAWL_<FIELD>` |
| `llm.py` | `LlmSettings` | `NEWS_AGENT_MODEL`, `NEWS_LLM_*`, `OPENROUTER_*`, `OPENAI_*`; `llm_provider()` / `llm_token()` / `llm_base_url()` |

Notes: a new group = a new module here + a field on `Settings` + a row in this table.
Keep a group about one concern; if two services need the same variable, it is one group,
not two copies. `WebCrawlSettings` doubles as the crawl's runtime configuration object —
the pipeline receives it whole, so a knob is set once (env or `model_copy(update=…)` in
`deps`) and read everywhere.
