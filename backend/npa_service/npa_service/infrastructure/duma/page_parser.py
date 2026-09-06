"""Parse bill metadata, progress, dates, and the latest Word text link."""

import re
from datetime import datetime
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup, Tag

from npa_service.application.errors import InvalidNpaPageError
from npa_service.domain import BillPage

MOSCOW = ZoneInfo("Europe/Moscow")
PUBLISHED_STAGE_CODE = "arrh_d11"
TEXT_MARKERS = (
    "текст внесенного законопроекта",
    "текст законопроекта",
    "текст принятого закона",
    "текст федерального закона",
)


def _current_stage(stages: list[Tag]) -> Tag:
    populated = [stage for stage in stages if stage.select_one(".oz_event[data-eventdate]")]
    if not populated:
        raise InvalidNpaPageError("bill has no dated consideration stage")
    return populated[-1]


def _event_dates(root: Tag) -> list[datetime]:
    dates = [
        _parse_date(str(node.get("data-eventdate"))) for node in root.select("[data-eventdate]")
    ]
    valid_dates = [value for value in dates if value is not None]
    if not valid_dates:
        raise InvalidNpaPageError("bill has no valid update date")
    return valid_dates


def _parse_date(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed.replace(tzinfo=MOSCOW) if parsed.tzinfo is None else parsed


def _bill_number(soup: BeautifulSoup) -> str:
    node = soup.select_one("#number_oz_id")
    match = re.search(r"\d+-\d+", node.get_text(" ", strip=True) if node else "")
    if match is None:
        raise InvalidNpaPageError("bill number was not found")
    return match.group(0)


def _title(soup: BeautifulSoup, title_node: Tag) -> str:
    title = title_node.get_text(" ", strip=True)
    comment = soup.select_one("#oz_name_comment")
    suffix = comment.get_text(" ", strip=True) if comment else ""
    return " ".join(part for part in (title, suffix) if part)


def _stage_name(stage: Tag) -> str:
    node = stage.select_one(".ttl .lnk")
    if node is None:
        raise InvalidNpaPageError("current bill stage has no name")
    return node.get_text(" ", strip=True)


def _latest_word_text(stages: list[Tag], page_url: str) -> str:
    candidates: list[tuple[int, datetime, str]] = []
    for index, stage in enumerate(stages):
        candidates.extend(_stage_documents(stage, index))
    if not candidates:
        raise InvalidNpaPageError("bill has no supported Word text document")
    _, _, path = max(candidates, key=lambda value: (value[0], value[1]))
    return urljoin(page_url, path)


def _stage_documents(stage: Tag, index: int) -> list[tuple[int, datetime, str]]:
    documents: list[tuple[int, datetime, str]] = []
    for link in stage.select("a.a_event_files"):
        label = link.get_text(" ", strip=True).lower()
        icon = link.select_one(".format-msword")
        event = link.find_parent(class_="oz_event")
        date = _parse_date(str(event.get("data-eventdate"))) if isinstance(event, Tag) else None
        if icon and date and any(marker in label for marker in TEXT_MARKERS):
            documents.append((index, date, str(link.get("href"))))
    return documents


def _published_at(stage: Tag) -> datetime | None:
    if stage.get("id") != PUBLISHED_STAGE_CODE:
        return None
    dates = _event_dates(stage)
    return max(dates)


class DumaPageParser:
    def parse(self, html: str, url: str) -> BillPage:
        soup = BeautifulSoup(html, "html.parser")
        history = soup.select_one("#bh_histras #oz_stages")
        title_node = soup.select_one("#oz_name")
        if history is None or title_node is None:
            raise InvalidNpaPageError("State Duma bill card was not found")

        stages = history.select(".root-stage")
        stage = _current_stage(stages)
        dates = _event_dates(history)
        number = _bill_number(soup)
        document_url = _latest_word_text(stages, url)
        published_at = _published_at(stage)
        return BillPage(
            url=url,
            bill_number=number,
            title=_title(soup, title_node),
            stage=_stage_name(stage),
            stage_code=str(stage.get("id")),
            document_url=document_url,
            updated_at=max(dates),
            published_at=published_at,
        )
