from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from common.core.settings import WebCrawlSettings
from source_service.application.ports.scraping import FetchedPage
from source_service.application.services.scraping import CardCollection
from source_service.domain import ArticleStatus, Hub, HubOrigin

FRESH = datetime.now(ZoneInfo("Europe/Moscow")).isoformat()
LISTING = f"""
<main>
  <article><a href="/content/new-story-with-a-long-slug">Fresh important news story</a><time datetime="{FRESH}">today</time></article>
  <article><a href="/content/old-story-with-a-long-slug">Old important news story</a><time datetime="2020-08-20T12:00:00+03:00">20.08.2020</time></article>
  <article><a href="/content/never-reached-story-slug">Never reached story here</a></article>
  <a rel="next" href="?page=2">Дальше</a>
</main>
"""


class FakeCrawler:
    def __init__(self):
        self.requested: list[str] = []

    async def crawl_page(self, url):
        self.requested.append(url)
        return FetchedPage(
            url=url, final_url=url, html=LISTING, markdown="", title="News", links=()
        )

    async def crawl_pages(self, urls):
        return []

    async def crawl_articles(self, urls):
        return []

    async def adaptive_discover(self, seed):
        return []

    async def best_first_discover(self, hub):
        return
        yield


@pytest.mark.asyncio
async def test_cards_are_collected_in_order_and_the_first_old_card_ends_the_hub():
    crawler = FakeCrawler()
    hub = Hub.build("https://example.test/news", HubOrigin.LISTING, "News")

    cards = await CardCollection(crawler, WebCrawlSettings(days=3)).run([hub])

    assert [c.url for c in cards] == ["https://example.test/content/new-story-with-a-long-slug"]
    assert cards[0].status is ArticleStatus.DISCOVERED
    assert cards[0].hub_url == hub.url
    assert cards[0].title_hint == "Fresh important news story"
    assert crawler.requested == [hub.url]  # stopped on the old card, never followed "Дальше"
