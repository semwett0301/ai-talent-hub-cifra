# domain/hub/rules

- `scoring.py` — `HUB_RULES` / `HUB_SCORER`: how much a page looks like a listing of
  publications — `HUB_TERMS` (news / press / blog / новости …, owned here) in the URL or
  title, a shallow path, several dated cards in the text excerpt (`DATE_LIKE_RE`, owned
  here); article markers (date in path, numeric id, deep long slug, very deep path) are
  penalties — the mirror image of the article rules. Built on the generic
  `domain.scoring` mechanism and the shared URL vocabulary in `domain.scoring.terms`.

- `ranking.py` — `hub_score`, `rank_hubs` (best first).

Notes: the acceptance threshold (`listing_llm_min_confidence`) is the use case's, not the
rule's — `HUB_SCORER` only orders candidates, `HubDiscovery` decides how strict to be.
