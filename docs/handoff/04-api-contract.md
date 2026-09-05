# 04. API-контракт

API versioned: `/api/v1`. Все ответы JSON, даты ISO 8601 UTC, ошибки RFC 9457-like: `type`, `title`, `status`, `detail`, `traceId`.

## News

`GET /news?query=&kind=news&attention=true&period=24h&cursor=` — курсорная лента. Ответ содержит `items`, `nextCursor`; score приходит технически, UI показывает только band.

`GET /news/{id}` — подробности и последнее AI-саммари.

`PATCH /news/{id}/state` — `{ hidden: true }`; персональное состояние пользователя.

`PUT /news/{id}/summary-override` — `{ summary }`; сохраняет редакцию с автором и timestamp.

## NPA

`GET /npa?mode=registry|updates&query=&cursor=` — реестр или только НПА с новыми изменениями.

`GET /npa/{id}` — карточка, версии, changes и AI-results.

`GET /alerts?kind=npa_signal&query=&cursor=` — новости/сигналы о готовящихся или изменённых законах.

`POST /npa` — один из вариантов:

```json
{ "source": { "type": "url", "url": "https://example.gov/law/123" } }
```

или

```json
{ "source": { "type": "upload", "documentId": "uuid" } }
```

`POST /uploads` — выдаёт `uploadUrl`, `documentId`, ограничения на MIME, размер и TTL. Клиент загружает PDF в object storage, затем вызывает `POST /npa` с `documentId`. Не принимать файл через обычный JSON API.

`GET /npa/{id}/changes/{changeId}` — возвращает краткое объяснение статьи, доказательные фрагменты и статус генерации.

## Sources

`GET /sources`

`POST /sources` — `{ name, url, type, frequencyCode, enabled }`.

`PATCH /sources/{id}` — изменение `enabled`/`frequencyCode`; смена URL лучше отдельной командой с повторной валидацией.

Разрешённые `frequencyCode`: `30m`, `1h`, `3h`, `8h`, `24h`, `3d`, `1w`, `1mo`, `1q`.

## Контракт read-models

Не отдавать UI сырые сущности БД. BFF должен собирать read-model, например `NewsCardDTO`, `NewsDetailDTO`, `NpaListItemDTO`, `NpaDetailDTO`, `SourceDTO`; это уменьшает связь UI с эволюцией хранения и LLM.

## Авторизация и права

- `viewer`: чтение;
- `analyst`: скрытие/редактирование саммари;
- `editor`: добавление НПА и управление источниками;
- `admin`: удаление, workspace и доступы.

Каждая команда должна проверять `workspace_id` на сервере, а не доверять ID из клиента.
