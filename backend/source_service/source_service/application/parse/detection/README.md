# parse/detection

Recognise a link's kind from the link alone, before any crawling. Used by
`SourceService.__detect_type` to pick a source's `SourceType`.

- `telegram.py` — `is_telegram_link(link)`: `tg://` deep links or
  `https://t.me/` / `https://telegram.me/` links.

Notes: RSS is not detected here — finding a site's feeds means crawling it, so that is
the `RssFeedFinder` port (`application/ports/scraping`), implemented in
`infrastructure/parsing`.
