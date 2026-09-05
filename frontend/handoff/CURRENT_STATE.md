# Current state

## Уже реализовано во frontend

Routes:

- /news
- /npa
- /sources

### News
- лента новостей
- поиск и фильтры
- detail view
- AI summary
- why important
- скрытие
- редактирование summary

### NPA
- реестр
- alerts
- updates
- diff изменений
- impact
- добавление через URL/PDF modal

### Sources
- список источников
- enabled switch
- frequency
- добавление источника

## Сейчас работает на mock data

- news
- NPA
- sources
- relevance
- AI summaries
- NPA changes

Mock data:
`frontend/src/data/*`

## Demo persistence

Состояние сейчас хранится через:

`frontend/src/hooks/useSessionState.ts`

и sessionStorage.

## Требуется backend integration

- News API
- NPA API
- Sources API
- PostgreSQL
- source ingestion
- NPA versioning/diff
- LLM processing
- PDF upload
- authentication/workspace

## Integration references

API:
`frontend/handoff/04-api-contract.md`

OpenAPI:
`frontend/handoff/openapi.yaml`

Delivery plan:
`frontend/handoff/06-delivery-plan.md`