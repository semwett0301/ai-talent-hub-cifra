# 06. План внедрения и приёмка

## Этап 0 — foundation

- SSO/RBAC, workspace, PostgreSQL, migrations, object storage, observability.
- Заменить `src/data/*` API-клиентом; заменить `useSessionState` query-кэшем и мутациями.
- Ввести skeleton/error/empty состояния на всех экранах.

## Этап 1 — Sources и ingestion

- CRUD источников, валидация URL, frequency scheduler, source runs.
- Один RSS/сайт-коннектор как вертикальный срез.
- Приёмка: переключение отслеживания прекращает будущие запуски; изменение частоты меняет `next_run_at`; дубликат URL отклоняется.

## Этап 2 — News

- Лента с курсорной пагинацией, поиск, фильтры, band релевантности, скрытие и summary override.
- Приёмка: default sort по score; score не показан; скрытие имеет audit record и не удаляет исходник; override не перезаписывает LLM-result.

## Этап 3 — NPA

- Реестр, URL upload и PDF upload, версии, diff, changes, алерты.
- Приёмка: API отклоняет одновременные URL и PDF; новый PDF создаёт version; отсутствие семантических изменений даёт «Изменений нет»; обновления содержат только изменённые НПА.

## Этап 4 — AI и эксплуатация

- LLM gateway, citations, review workflow, мониторинг качества, алерты на ошибки.
- Приёмка: каждый вывод имеет model/prompt/source version; ответ без валидной схемы не публикуется; оператор может увидеть первоисточник.

## Обязательные тесты

- Unit: scoring bands, фильтры, URL/PDF exclusivity, frequency mapping, permission checks.
- Integration: upload → processing → NPA version → change → alert.
- E2E: News hide/edit, Source frequency, NPA add URL/PDF, alert-to-tracking flow.
- Security: signed upload TTL, workspace isolation, MIME/magic byte, malware scan, SSRF prevention для URL-fetch.
- Load: параллельный ingestion без duplicate news/version; degraded behaviour при недоступной модели/источнике.

## Известные отличия прототипа от production

Mock даты, источники и юридические изменения не являются фактами. В UI PDF сейчас выбирается локально, но не загружается; серверная загрузка описана в API. Текущий ручной текст «LLM» — демонстрационный: в production он должен быть результатом versioned pipeline с цитатами.
