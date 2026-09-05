# 03. Модель данных

## Основные таблицы

| Таблица | Ключевые поля | Назначение |
| --- | --- | --- |
| `workspaces` | `id`, `name` | Изоляция данных организации/команды. |
| `users`, `workspace_members` | `user_id`, `role` | Доступ и аудит. |
| `sources` | `id`, `workspace_id`, `url`, `type`, `frequency_code`, `enabled` | Конфигурация источников. |
| `source_runs` | `source_id`, `started_at`, `status`, `error` | История запусков сборщика. |
| `documents` | `id`, `sha256`, `storage_key`, `mime_type`, `text` | Исходные PDF/HTML и извлечённый текст. |
| `news_items` | `id`, `source_id`, `published_at`, `title`, `body`, `relevance_score`, `classification` | Нормализованная публикация. |
| `news_ai_results` | `news_id`, `summary`, `impact`, `model_version`, `prompt_version` | Результат модели, отдельно от пользовательских правок. |
| `news_user_states` | `news_id`, `user_id`, `hidden_at`, `edited_summary` | Персональные действия в ленте. |
| `npa_tracking` | `id`, `workspace_id`, `canonical_url`, `title`, `status` | Реестр отслеживаемых НПА. |
| `npa_versions` | `tracking_id`, `document_id`, `version_hash`, `checked_at` | Последовательность версий. |
| `npa_changes` | `from_version_id`, `to_version_id`, `article_ref`, `before_text`, `after_text` | Структурированные изменения. |
| `npa_ai_results` | `npa_change_id`, `explanation`, `overall_summary`, `impact` | LLM-пояснения и общий вывод. |
| `alerts` | `workspace_id`, `news_id`, `npa_tracking_id`, `kind`, `status` | Сигналы о НПА. |
| `audit_log` | `actor_id`, `entity_type`, `entity_id`, `action`, `before`, `after` | Аудит команд пользователя. |

## Ограничения и индексы

- `sources(workspace_id, normalized_url)` — unique.
- `documents.sha256` — unique для бинарного дедуплицирования.
- `news_items(source_id, external_id)` — unique, если источник даёт ID; иначе fingerprint заголовка/даты/текста.
- `npa_versions(tracking_id, version_hash)` — unique.
- Индексы: `news_items(workspace_id, published_at DESC)`, `news_items(relevance_score DESC)`, GIN/tsvector для поиска, `npa_tracking(workspace_id, status)`.

## Статусы

`source_runs`: `queued | running | succeeded | partial | failed`.

`npa_tracking.status`: `active | paused | archived | processing | failed`.

`alerts.status`: `new | reviewed | dismissed | linked_to_npa`.

`npa_changes.review_status`: `new | confirmed | ignored`.

## JSON-формат результата LLM

Все ответы модели валидируются схемой до сохранения. Минимум: `summary`, `impact`, `confidence` (0–1), `citations[]` с fragment offsets. Для изменений статьи дополнительно: `article_ref`, `plain_language_explanation`, `materiality`.
