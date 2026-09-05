# domain/hub

The hub aggregate: a page that lists publications — a news section, a press centre, a
blog index. A hub is never published; it is where article links are read from. The root
holds only the entity; its sub-models are in `model/`, its rules in `rules/`.

- `hub.py` — `Hub`: url, `origin`, optional title, a bounded `text_excerpt` of the page
  (the dated-cards rule reads it) and `next_page` — the second listing page when the
  classifier pointed at one. `identity` folds pagination variants into one hub.
  `Hub.build(url, origin, title, text, next_page)` trims the excerpt to `TEXT_EXCERPT_LIMIT`.
- `model/` — `HubOrigin`. See `model/README.md`.
- `rules/` — `HUB_SCORER`: how much a page looks like a listing. See `rules/README.md`.

Notes: compare hubs by `identity`, never by raw URL. Scores come from `HUB_SCORER`, never
from a field.
