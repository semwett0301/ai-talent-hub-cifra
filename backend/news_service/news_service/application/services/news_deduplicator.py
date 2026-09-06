"""Persistent, precision-first event clustering after every summary has been stored."""

import uuid
from dataclasses import dataclass, field

from common.core.logging import get_logger
from common.core.settings import NewsDedupSettings

from news_service.application.ports import DedupRepository, EventModels
from news_service.domain.dedup import (
    CandidateQuery,
    ClusterAssignment,
    EventSummary,
    MembershipDecision,
    Precluster,
)
from news_service.domain.dedup.membership_decision import Decision
from news_service.domain.dedup.policy import (
    combine_decisions,
    find_time_conflicts,
    normalize_decision,
)

logger = get_logger(__name__)


@dataclass(slots=True)
class _CandidatePlan:
    cluster_id: uuid.UUID
    decision: Decision | None = None


@dataclass(slots=True)
class _NewsPlan:
    summary: EventSummary
    candidates: list[_CandidatePlan] = field(default_factory=list)


@dataclass(slots=True)
class _AlignmentGroup:
    anchors: tuple[EventSummary, ...]
    candidates: list[EventSummary] = field(default_factory=list)


class NewsDeduplicator:
    def __init__(
        self,
        repository: DedupRepository,
        models: EventModels,
        config: NewsDedupSettings,
    ) -> None:
        self.__repository = repository
        self.__models = models
        self.__config = config

    async def process(self, summaries: list[EventSummary]) -> None:
        if not summaries:
            logger.info("news dedup skipped: reason=no_pending_summaries")
            return

        ordered = sorted(summaries, key=_summary_order)
        plans, groups = await self.__plan(ordered)
        await self.__align(plans, groups)
        assignments = self.__assign(plans)
        await self.__repository.assign_clusters(assignments)

        created = sum(assignment.news_id == assignment.cluster_id for assignment in assignments)
        logger.info(
            "news batch deduplicated: items=%d new_clusters=%d attached=%d",
            len(assignments),
            created,
            len(assignments) - created,
        )

    async def __plan(
        self, summaries: list[EventSummary]
    ) -> tuple[list[_NewsPlan], dict[uuid.UUID, _AlignmentGroup]]:
        plans: list[_NewsPlan] = []
        groups: dict[uuid.UUID, _AlignmentGroup] = {}
        previous_ids: list[uuid.UUID] = []
        for summary in summaries:
            plan = await self.__plan_summary(summary, tuple(previous_ids), groups)
            plans.append(plan)
            previous_ids.append(summary.news_id)
        return plans, groups

    async def __plan_summary(
        self,
        summary: EventSummary,
        previous_ids: tuple[uuid.UUID, ...],
        groups: dict[uuid.UUID, _AlignmentGroup],
    ) -> _NewsPlan:
        plan = _NewsPlan(summary)
        if not summary.has_primary_event:
            return plan

        query = CandidateQuery(
            summary=summary,
            available_pending_ids=previous_ids,
            window_days=self.__config.candidate_window_days,
            limit=self.__config.top_k_candidates,
            minimum_score=self.__config.min_retrieval_score,
        )
        for candidate in await self.__repository.find_candidates(query):
            candidate_plan = _CandidatePlan(candidate.cluster_id)
            conflicts = find_time_conflicts(
                summary, candidate.anchors, self.__config.hard_time_tolerance_days
            )
            if conflicts:
                candidate_plan.decision = "DIFFERENT"
            else:
                group = groups.setdefault(candidate.cluster_id, _AlignmentGroup(candidate.anchors))
                group.candidates.append(summary)
            plan.candidates.append(candidate_plan)
        return plan

    async def __align(
        self,
        plans: list[_NewsPlan],
        groups: dict[uuid.UUID, _AlignmentGroup],
    ) -> None:
        preclusters = [
            Precluster(cluster_id, group.anchors, tuple(group.candidates))
            for cluster_id, group in groups.items()
        ]
        responses = await self.__models.align(preclusters)
        decisions = {
            precluster.cluster_id: response
            for precluster, response in zip(preclusters, responses, strict=True)
        }
        for plan in plans:
            self.__apply_decisions(plan, decisions)

    @staticmethod
    def __apply_decisions(
        plan: _NewsPlan,
        decisions: dict[uuid.UUID, dict[uuid.UUID, MembershipDecision]],
    ) -> None:
        for candidate in plan.candidates:
            if candidate.decision is not None:
                continue
            response = decisions.get(candidate.cluster_id, {}).get(plan.summary.news_id)
            candidate.decision = normalize_decision(response) if response else "UNCERTAIN"

    def __assign(self, plans: list[_NewsPlan]) -> list[ClusterAssignment]:
        resolved: dict[uuid.UUID, uuid.UUID] = {}
        assignments: list[ClusterAssignment] = []
        for plan in plans:
            cluster_id = self.__choose_cluster(plan, resolved)
            resolved[plan.summary.news_id] = cluster_id
            assignments.append(ClusterAssignment(plan.summary.news_id, cluster_id))
        return assignments

    def __choose_cluster(self, plan: _NewsPlan, resolved: dict[uuid.UUID, uuid.UUID]) -> uuid.UUID:
        combined: dict[uuid.UUID, list[Decision]] = {}
        for candidate in plan.candidates:
            cluster_id = resolved.get(candidate.cluster_id, candidate.cluster_id)
            combined.setdefault(cluster_id, []).append(candidate.decision or "UNCERTAIN")

        decisions = {
            cluster_id: combine_decisions(values) for cluster_id, values in combined.items()
        }
        same = [cluster_id for cluster_id, decision in decisions.items() if decision == "SAME"]
        has_uncertain = any(decision == "UNCERTAIN" for decision in decisions.values())
        if len(same) == 1 and not (
            self.__config.reject_if_any_uncertain_candidate and has_uncertain
        ):
            return same[0]
        return plan.summary.news_id


def _summary_order(summary: EventSummary) -> tuple[bool, float, int]:
    timestamp = summary.published_at.timestamp() if summary.published_at else 0.0
    return summary.published_at is None, timestamp, summary.news_id.int
