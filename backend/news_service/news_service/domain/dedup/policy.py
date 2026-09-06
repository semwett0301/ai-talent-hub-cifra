"""Fail-closed same-event policy independent of models and persistence."""

from datetime import UTC, datetime

from news_service.domain.dedup.event_summary import EventSummary
from news_service.domain.dedup.membership_decision import Decision, MembershipDecision

SECONDS_PER_DAY = 86_400


def find_time_conflicts(
    summary: EventSummary, anchors: tuple[EventSummary, ...], tolerance_days: int
) -> tuple[str, ...]:
    event_time = _event_time(summary)
    if event_time is None:
        return ()

    conflicts = (
        _time_conflict(event_time, _event_time(anchor), tolerance_days) for anchor in anchors
    )
    return tuple(conflict for conflict in conflicts if conflict is not None)


def normalize_decision(decision: MembershipDecision) -> Decision:
    if decision.hard_conflicts or decision.decision == "DIFFERENT":
        return "DIFFERENT"
    if decision.decision == "SAME" and not decision.critical_unknowns:
        return "SAME"
    return "UNCERTAIN"


def combine_decisions(decisions: list[Decision]) -> Decision:
    if decisions and all(decision == "SAME" for decision in decisions):
        return "SAME"
    if any(decision == "DIFFERENT" for decision in decisions):
        return "DIFFERENT"
    return "UNCERTAIN"


def _event_time(summary: EventSummary) -> datetime | None:
    event_time = summary.extraction.get("event_time")
    if not isinstance(event_time, dict) or event_time.get("precision") not in {"day", "datetime"}:
        return None

    value = event_time.get("start")
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _time_conflict(
    event_time: datetime, anchor_time: datetime | None, tolerance_days: int
) -> str | None:
    if anchor_time is None:
        return None
    gap_days = abs((event_time - anchor_time).total_seconds()) / SECONDS_PER_DAY
    if gap_days <= tolerance_days:
        return None
    return f"explicit event times differ by {gap_days:.1f} days (> {tolerance_days})"
