"""State-pattern and monitoring tests with no network or model calls."""

import uuid
from datetime import UTC, datetime

from common.entities.npa import NpaTrackingStatus
from common.schemas import Npa
from npa_service.application.services import NpaMonitor, NpaRegistration
from npa_service.domain import ArticleChange, BillSnapshot, ChangeSummary, TrackedUpdate
from npa_service.domain.state import build_tracking_state
from npa_service.infrastructure.simulation.simulation_source import SIMULATION_URL, SimulationSource

URL = "https://sozd.duma.gov.ru/bill/1-8"


async def test_registration_stops_when_bill_is_already_published() -> None:
    repo = _Repo()
    stored = await NpaRegistration(repo, _Source(_snapshot("arrh_d11", "text", True))).register(
        URL
    )

    assert stored.tracking_status == NpaTrackingStatus.PUBLISHED
    assert repo.added_status == NpaTrackingStatus.PUBLISHED
    assert not build_tracking_state(stored.tracking_status).can_check


async def test_monitor_versions_changes_and_stops_after_publication() -> None:
    current = _row("arrh_d4", "old text")
    repo = _Repo(current)
    article = ArticleChange("Статья 1", "Срок короче", "30", "10")
    summary = ChangeSummary("Правило стало проще.", (article,))
    monitor = NpaMonitor(repo, _Source(_snapshot("arrh_d11", "new text", True)), _Model(summary))

    await monitor.check(current.id)

    assert repo.update_value is not None
    assert repo.update_value.status == NpaTrackingStatus.PUBLISHED
    assert repo.update_value.change == summary


async def test_monitor_skips_model_for_unchanged_state() -> None:
    current = _row("arrh_d4", "same text")
    repo = _Repo(current)
    model = _Model(ChangeSummary("unused", ()))

    await NpaMonitor(repo, _Source(_snapshot("arrh_d4", "same text")), model).check(current.id)

    assert repo.was_checked
    assert not model.was_called


async def test_simulation_source_advances_to_publication() -> None:
    source = SimulationSource()

    initial = await source.fetch(SIMULATION_URL)
    changed = await source.fetch(SIMULATION_URL)
    published = await source.fetch(SIMULATION_URL)

    assert initial.stage_code == "arrh_d4"
    assert changed.text != initial.text
    assert published.is_published


async def test_simulation_source_starts_each_url_from_initial_version() -> None:
    source = SimulationSource()

    await source.fetch(SIMULATION_URL)
    other = await source.fetch("https://sozd.duma.gov.ru/bill/9999999-10")

    assert other.stage_code == "arrh_d4"


class _Source:
    def __init__(self, snapshot: BillSnapshot) -> None:
        self.snapshot = snapshot

    async def fetch(self, url: str) -> BillSnapshot:
        return self.snapshot


class _Model:
    def __init__(self, summary: ChangeSummary) -> None:
        self.summary = summary
        self.was_called = False

    async def summarize(self, previous_text: str, current_text: str) -> ChangeSummary:
        self.was_called = True
        return self.summary


class _Repo:
    def __init__(self, row: Npa | None = None) -> None:
        self.row = row
        self.added_status: NpaTrackingStatus | None = None
        self.update_value: TrackedUpdate | None = None
        self.was_checked = False

    async def list_all(self, limit: int, offset: int) -> list[Npa]:
        return [self.row] if self.row else []

    async def get(self, npa_id: uuid.UUID) -> Npa | None:
        return self.row

    async def list_tracking(self) -> list[Npa]:
        return [self.row] if self.row else []

    async def list_versions(self, npa_id: uuid.UUID) -> list:
        return []

    async def add(self, snapshot: BillSnapshot, status: NpaTrackingStatus) -> Npa:
        self.added_status = status
        self.row = _row(snapshot.stage_code, snapshot.text, status)
        return self.row

    async def apply_update(self, npa_id: uuid.UUID, update_value: TrackedUpdate) -> Npa:
        self.update_value = update_value
        self.row = _row(
            update_value.snapshot.stage_code, update_value.snapshot.text, update_value.status
        )
        return self.row

    async def mark_checked(
        self, npa_id: uuid.UUID, snapshot: BillSnapshot, checked_at: datetime
    ) -> None:
        self.was_checked = True


def _snapshot(stage_code: str, text: str, is_published: bool = False) -> BillSnapshot:
    observed = datetime(2026, 9, 6, tzinfo=UTC)
    return BillSnapshot(
        URL,
        "1-8",
        "Test bill",
        "Stage",
        stage_code,
        text,
        f"https://sozd.duma.gov.ru/download/{stage_code}",
        observed,
        observed if is_published else None,
    )


def _row(
    stage_code: str,
    text: str,
    status: NpaTrackingStatus = NpaTrackingStatus.TRACKING,
) -> Npa:
    return Npa(
        id=uuid.uuid4(),
        url=URL,
        title="Test bill",
        text=text,
        stage="Stage",
        stage_code=stage_code,
        document_url=f"https://sozd.duma.gov.ru/download/{stage_code}",
        tracking_status=status,
        article_changes=[],
    )
