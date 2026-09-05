# 07. Карта текущего frontend-кода

Репозиторий UI: `C:\Users\U_M2W6Z\Desktop\Учеба_ИТМО\gs-labs-monitoring-ui`.

| Путь | Что находится |
| --- | --- |
| `src/App.tsx` | Application shell, sidebar, React Router routes. |
| `src/App.css` | Тёмная тема, responsive layout, все product-level стили. |
| `src/pages/NewsPage.tsx` | Лента новостей, фильтры, скрытие и редактирование саммари. |
| `src/pages/NpaPage.tsx` | Реестр НПА, алерты, обновления, изменения статей и URL/PDF modal. |
| `src/pages/SourcesPage.tsx` | Источники, частота и включение отслеживания. |
| `src/data/news.ts`, `npa.ts`, `sources.ts` | Mock fixtures, которые нужно заменить API client. |
| `src/types/monitoring.ts` | Временные frontend types; не использовать как схему БД без переработки. |
| `src/hooks/useSessionState.ts` | Demo persistence в `sessionStorage`; удалить после миграции на API/cache. |
| `src/components/ui/` | Базовые shadcn/Base UI primitives. |
| `src/components/monitoring/Shared.tsx` | `SearchField` и `Choice`; `FeatureStrip` больше не используется. |

## Рекомендуемая frontend-миграция

1. Добавить `src/api/` с типизированным HTTP client, DTO и mapping DTO → view model.
2. Добавить query-кэш (например, TanStack Query) для лент, деталей и мутаций.
3. Вынести экранные локальные состояния в URL: query, filter, period, selected item.
4. Не подменять server state оптимистично без rollback и `traceId` ошибки.
5. Сохранить текущие визуальные компоненты, но загрузить список/детали раздельно для независимого loading/error состояния.

## Минимальные frontend-доработки вместе с API

- Заменить `news`, `npa`, `initialSources` запросами.
- Получать `relevanceBand` с API или вычислять из server score единым shared function; score в UI не выводить.
- Сделать modal PDF upload через `POST /uploads` → PUT в signed URL → `POST /npa`.
- В деталях НПА показывать `processing` пока diff/LLM explanation не готов.
- В алертах использовать server relationship `alert → news_item → optional npa_tracking`.
