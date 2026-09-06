"""Public same-event deduplication domain API."""

from news_service.domain.dedup.candidate_cluster import CandidateCluster
from news_service.domain.dedup.candidate_query import CandidateQuery
from news_service.domain.dedup.cluster_assignment import ClusterAssignment
from news_service.domain.dedup.event_summary import EventSummary
from news_service.domain.dedup.membership_decision import MembershipDecision
from news_service.domain.dedup.news_target import NewsTarget
from news_service.domain.dedup.precluster import Precluster
from news_service.domain.dedup.prepared_news import PreparedNews
from news_service.domain.dedup.stored_news_state import StoredNewsState

__all__ = [
    "CandidateCluster",
    "CandidateQuery",
    "ClusterAssignment",
    "EventSummary",
    "MembershipDecision",
    "NewsTarget",
    "Precluster",
    "PreparedNews",
    "StoredNewsState",
]
