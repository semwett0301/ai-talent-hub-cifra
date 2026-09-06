"""Deterministic first-version overview for the local NPA demonstration."""

from npa_service.application.ports import InitialSummarizer
from npa_service.domain import BillSnapshot, InitialSummary


class SimulationInitialSummarizer(InitialSummarizer):
    async def summarize(self, snapshot: BillSnapshot) -> InitialSummary:
        return InitialSummary(
            title="Новые правила для цифровых сервисов",
            summary=(
                "Проект вводит единые требования к цифровым сервисам: как они обрабатывают "
                "данные пользователей и информируют их об условиях работы. Он затрагивает "
                "операторов сервисов и их клиентов; ключевое требование — закрепить эти правила "
                "внутренними процедурами."
            ),
        )
