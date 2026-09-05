from source_service.domain import (
    Article,
    Hub,
    HubOrigin,
    is_article_like,
    merge_hubs,
    select_candidates,
    select_hubs,
)


def test_select_candidates_keeps_article_like_urls_once_best_sighting_first():
    weak = Article(url="https://example.com/news/2026/09/03/long-slug-of-the-story")
    strong = weak.model_copy(update={"title_hint": "A headline that is long enough"})
    junk = Article(url="https://example.com/about/company")

    selected = select_candidates([weak, junk, strong], min_score=0.18)

    assert [a.url for a in selected] == [weak.url]
    assert selected[0].title_hint == strong.title_hint  # the better-scored sighting won
    assert not is_article_like(junk, 0.18)


def test_select_hubs_and_merge_hubs_rank_and_deduplicate():
    plain = Hub.build("https://example.com/press-center", HubOrigin.ADAPTIVE)
    titled = Hub.build(
        "https://example.com/press-center",
        HubOrigin.ADAPTIVE,
        "Press news",
        text="01.09.2026 · 02.09.2026 · 03.09.2026",  # dated cards: the richer sighting
    )
    article_like = Hub.build(
        "https://example.com/news/2026/09/03/long-slug-of-an-article-here", HubOrigin.ADAPTIVE
    )

    selected = select_hubs([plain, article_like, titled], min_score=0.35)
    merged = merge_hubs([plain, titled, article_like])

    assert [h.url for h in selected] == [plain.url]
    assert selected[0].title == "Press news"
    assert [h.url for h in merged] == [plain.url, article_like.url]
