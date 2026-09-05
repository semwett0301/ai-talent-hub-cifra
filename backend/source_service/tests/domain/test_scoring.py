from source_service.domain import (
    ARTICLE_SCORER,
    HUB_SCORER,
    Article,
    Hub,
    HubOrigin,
    RuleScorer,
    ScoreRule,
)


def test_article_score_names_the_rules_that_fired():
    score = ARTICLE_SCORER.score(
        Article(url="https://example.com/news/2026/09/03/long-important-company-announcement")
    )

    assert set(score.fired) == {
        "article_path",
        "date_in_path",
        "long_slug",
        "nested",
        "deeply_nested",
    }
    assert score.value == 0.75


def test_article_headline_and_metadata_rules_read_the_entity_state():
    bare = ARTICLE_SCORER.score(Article(url="https://example.com/p/1"))
    titled = ARTICLE_SCORER.score(
        Article(url="https://example.com/p/1", title_hint="A headline long enough to count")
    )
    with_metadata = ARTICLE_SCORER.score(
        Article(url="https://example.com/p/1", metadata={"og:type": "article"})
    )

    assert "headline" not in bare.fired
    assert {"headline", "long_headline"} <= set(titled.fired)
    assert "article_metadata" in with_metadata.fired


def test_junk_path_penalty_clamps_at_zero():
    score = ARTICLE_SCORER.score(Article(url="https://example.com/about/company"))
    assert "junk_path" in score.fired
    assert score.value == 0.0


def test_hub_score_rewards_sections_and_penalises_article_shaped_urls():
    section = HUB_SCORER.score(Hub.build("https://example.com/press-center", HubOrigin.SEED))
    article_like = HUB_SCORER.score(
        Hub.build(
            "https://example.com/news/2026/09/03/long-slug-of-an-article-here", HubOrigin.SEED
        )
    )

    assert {"hub_terms", "shallow"} <= set(section.fired)
    assert section.value >= 0.35
    assert {"date_in_path", "deep_long_slug", "very_deep"} <= set(article_like.fired)
    assert article_like.value == 0.0


def test_hub_dated_cards_rule_counts_dates_in_the_excerpt():
    text = "Новость 01.09.2026 · Новость 02.09.2026 · Новость 03.09.2026"
    hub = Hub.build("https://example.com/company", HubOrigin.SEED, text=text)
    assert "dated_cards" in HUB_SCORER.score(hub).fired


def test_rule_scorer_is_generic_over_the_entity():
    scorer: RuleScorer[str] = RuleScorer(
        [ScoreRule("long", 0.6, lambda s: len(s) > 3), ScoreRule("upper", 0.6, str.isupper)]
    )
    assert scorer.score("ABCD").value == 1.0
    assert scorer.score("ab").fired == ()
