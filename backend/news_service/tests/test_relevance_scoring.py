import pytest
from news_service.domain.event_cluster import RelevanceCategory
from news_service.domain.event_cluster.rules import calculate_relevance, categorize_relevance


@pytest.mark.parametrize(
    ("impact", "urgency", "category"),
    [
        (0, 0, RelevanceCategory.LOW),
        (1, 0, RelevanceCategory.RELEVANT),
        (2, 0, RelevanceCategory.IMPORTANT),
        (2, 3, RelevanceCategory.IMPORTANT),
        (3, 0, RelevanceCategory.ATTENTION),
    ],
)
def test_each_impact_grade_maps_to_one_category(
    impact: int, urgency: int, category: RelevanceCategory
):
    score = calculate_relevance(impact, urgency, source=2, bm25_score=0.0)

    assert categorize_relevance(score) is category


def test_urgency_only_counts_from_material_impact():
    assert calculate_relevance(1, 3, 2, 0.0) == calculate_relevance(1, 0, 2, 0.0)
    assert calculate_relevance(2, 3, 2, 0.0) > calculate_relevance(2, 0, 2, 0.0)
