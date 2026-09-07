"""Fail-closed same-event membership policy independent of models and persistence."""

from news_service.domain.event_cluster.model.membership_decision import (
    Decision,
    MembershipDecision,
)


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
