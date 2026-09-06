"""Deterministic first-version overview for the local NPA demonstration."""

from npa_service.application.ports import InitialSummarizer
from npa_service.domain import BillSnapshot


class SimulationInitialSummarizer(InitialSummarizer):
    async def summarize(self, snapshot: BillSnapshot) -> str:
        return (
            f"Законопроект «{snapshot.title}» задаёт правила в указанной сфере. "
            "Он важен для граждан и организаций, которых затрагивают предусмотренные в тексте "
            "права, обязанности и сроки. При оценке последствий стоит в первую очередь проверить "
            "круг адресатов, условия применения норм, исключения и дату вступления в силу. "
            "Это обзор первой доступной редакции: перед принятием решения сверяйтесь с официальным документом."
        )
