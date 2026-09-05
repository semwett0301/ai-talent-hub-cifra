# rabbit

RabbitMQ publishing — the `NewsPublisher` implementation (one class per module,
re-exported from `__init__.py`).

- `connector.py` — `RabbitConnector`: connects/declares the topic exchange;
  `publish_news` publishes each `common.entities.news.NewsDTO` to the `news` exchange with its
  per-type routing key.

Notes: inherits `application.ports.NewsPublisher` so mypy verifies the contract at the
definition site. Payload shape + routing are owned by `common.entities.news` (the shared contract),
not here.
