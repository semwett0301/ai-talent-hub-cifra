import uuid
from datetime import UTC, datetime

from news_service.domain.dedup import EventSummary, MembershipDecision
from news_service.domain.dedup.policy import find_time_conflicts, normalize_decision


def _summary(day: int) -> EventSummary:
    return EventSummary(
        uuid.uuid4(),
        "https://news.test",
        "summary",
        {
            "primary_event_found": True,
            "event_time": {"start": f"2026-09-{day:02d}", "precision": "day"},
        },
        datetime(2026, 9, day, tzinfo=UTC),
    )


def test_time_gate_rejects_explicit_events_outside_tolerance():
    assert find_time_conflicts(_summary(5), (_summary(1),), tolerance_days=1)


def test_same_with_a_critical_unknown_fails_closed():
    decision = MembershipDecision("SAME", critical_unknowns=("lifecycle stage",))
    assert normalize_decision(decision) == "UNCERTAIN"
