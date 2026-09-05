# services/web/listings

From the hubs `hubs/` found to the candidate links their listing pages print. Reading a
listing is all that happens here — finding one is `hubs/`, opening an article is `articles/`.

- `card_collection.py` — `CardCollection.run(hubs) -> list[Article]` (`DISCOVERED`): each
  hub page after page, cards in order; the first card dated before the window ends the hub;
  next page = `hub.next_page` for the first hop, then `next_listing_page`. Dedupes by card
  URL (first sighting wins) *before* the `max_article_candidates_per_site` cap, so the cap
  counts distinct articles.

Notes: pagination never reaches the orchestrator — `CardCollection` walks it internally,
the same way `ArticleHarvest` keeps article batching to itself.
