# hubs/state

State that belongs to **one site crawl**, not to the service. `HubDiscovery` builds these
at the top of `run()` and threads them down as parameters — one instance serves every site
the scheduler crawls, often several at once, so nothing here may be stored on `self` or
injected from `deps.py`.

- `frontier.py` — `Frontier`: which listing URLs of this site have already been fetched.
  `take(urls)` hands back the ones nobody has seen and records them in the same call, so a
  page can never be handed out twice; capped at `listing_max_pages_per_site` (0 = no cap).

Notes: identity is `listing_identity(url)`, so pagination variants count as one page.
