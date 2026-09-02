# src

- `main.tsx` — entry; mounts `<App>` inside `<BrowserRouter>`.
- `App.tsx` — layout + route table (`<Routes>`).
- `pages/` — one component per route.
- `assets/` — imported assets (bundled/hashed).
- `index.css`, `App.css` — global and app styles.

Notes: routes are declared in `App.tsx`; add a page in `pages/` and wire it there.
