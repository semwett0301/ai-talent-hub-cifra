# GS Labs — UI prototype

Implemented in the existing React application using its installed dependencies. No backend or new runtime dependencies were added.

## Run

```sh
npm run dev
npm run build
npm run lint
```

Open the localhost URL printed by Vite. `/` redirects to `/news`.

## Screens

- `/news`: typed news fixtures, text/tag/source search, type and attention filters, 24-hour/week window, selection, AI summary editing, hide/restore, digest and tracking flags.
- `/npa`: typed document fixtures, search, control/update/alert filters, deadline window, before/after comparison, version history, owner assignment, control and digest flags.
- `/sources`: six initial sources, enable/disable, add source with name/URL/type/frequency, URL and duplicate validation, monitoring and NPA rule switches.

Actions are persisted in the current browser tab's sessionStorage. Reloading and route navigation preserve actions; closing the tab ends the session. Search and filter controls reset when navigating away. Storage failures fall back to in-memory state. A new tab gives a fresh demonstration.

## Files

- `src/App.tsx`: shared shell, navigation and route definitions.
- `src/App.css`: reference-based dark palette, dense layout and responsive styles.
- `src/pages/`: News, NPA and Sources screen compositions.
- `src/components/monitoring/Shared.tsx`: shared search, selection and feature strip.
- `src/components/ui/`: existing shadcn/Base UI primitives, unchanged.
- `src/data/`: typed demonstration fixtures; no datasets inside pages.
- `src/types/monitoring.ts`: entity types.
- `src/hooks/useSessionState.ts`: browser-session persistence.

## Scope

All news, legal changes, dates, relevance scores and AI summaries are illustrative mock content. Source URLs are fixture values: no requests are made to them. Adding a source does not start ingestion. Rule switches save prototype settings; they do not schedule jobs or alter the fixed datasets. Digest and tracking buttons set local flags; generating or sending a digest is not included. Owner assignment does not notify anyone. Backend integration, authentication, live AI and actual source-document links remain outside this prototype.

The three supplied images informed the layout, color system and content hierarchy. Additional sidebar sections shown in the references were omitted because this iteration covers only News, NPA and Sources. On narrow screens the detail panel moves below the list.

## Validation

- Original scaffold build passed before implementation.
- Production builds passed after News and NPA and after all three screens.
- ESLint passed; generated style exports are allowed only for button/badge/tabs primitives.
- Browser checks covered editing/hiding/restoring news, empty search, NPA version history and owner assignment, removing/restoring control, source URL validation and addition, switches, interval selection and persistence after reload.
- Mobile check at 390px: fixed horizontal overflow, inspected News and Sources.
- Browser error log was empty during interaction checks.
