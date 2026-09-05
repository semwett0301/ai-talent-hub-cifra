# domain/site

The site aggregate: the `WEB` source a crawl runs against. No sub-models or rule sets yet,
so the entity module is the whole package.

- `site.py` — `Site`: entry `url`, optional `name`, `enabled`, `allowed_domains`.
  `seed` is the normalised entry URL every crawl starts from, `label` what logs call the
  site, and `owns(url)` answers "does this link stay on the site?" — the entry host and
  its subdomains, plus any allowed domain.

Notes: `owns` is the one place the same-site rule is applied; discovery never compares
hosts itself. A `Site` is built by the collector from the `Source` row (`link`, `name`).
