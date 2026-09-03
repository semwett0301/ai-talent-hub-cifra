# rabbit

RabbitMQ publishing — the `NewsPublisher` implementation (one class per module,
re-exported from `__init__.py`).

- `connector.py` — `RabbitConnector`: connects/declares the topic exchange;
  `publish_news` maps `NewsItem` → `common.dto.NewsDTO` and publishes to the `news`
  exchange with the per-type routing key.

Notes: structurally satisfies `application.ports.NewsPublisher`. Payload shape +
routing are owned by `common.dto` (the shared contract), not here.
