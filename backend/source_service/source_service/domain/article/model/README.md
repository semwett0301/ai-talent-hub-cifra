# domain/article/model

What an `Article` carries, stage by stage, and the enums that name its lifecycle.

- `status.py` — `ArticleStatus` (discovered → fetched → dated → accepted | rejected),
  `RejectReason` (fetch failed, too short, not an article, no date, out of window, no title),
  `ArticleOrigin` (which discovery step found the link).
- `content.py` — `ArticleContent`: body text, word count, the page's own metadata
  (title, author, section, language, image, canonical URL, modified/fetched times) and
  raw provenance under `metadata`. Attached at `FETCHED`.
- `publication.py` — `PublicationDate`: value, `source` (a label naming the extraction
  technique — that vocabulary belongs to the use case), confidence, evidence. Attached
  at `DATED`.

Notes: all frozen pydantic models; none of them knows the entity that carries them. What
the listing card said (`title_hint`, `card_published_at`) stays on the entity itself — it
is known before any fetch.
