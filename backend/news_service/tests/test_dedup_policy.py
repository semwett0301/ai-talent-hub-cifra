from news_service.domain.event_cluster import MembershipDecision
from news_service.domain.event_cluster.rules import normalize_decision


def test_same_with_a_critical_unknown_fails_closed():
    decision = MembershipDecision("SAME", critical_unknowns=("lifecycle stage",))
    assert normalize_decision(decision) == "UNCERTAIN"
