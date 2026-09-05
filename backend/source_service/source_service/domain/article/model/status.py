"""Lifecycle of a web article: where it is in the crawl and why it was dropped."""

from enum import StrEnum


class ArticleStatus(StrEnum):
    """Stages an article passes through; every stage adds data, `REJECTED` is terminal."""

    DISCOVERED = "discovered"  # a link taken from a hub, nothing fetched yet
    FETCHED = "fetched"  # the page is downloaded: text and metadata are known
    DATED = "dated"  # a trustworthy publication date is resolved
    ACCEPTED = "accepted"  # fresh and titled: ready to publish
    REJECTED = "rejected"


class RejectReason(StrEnum):
    """Why an article left the pipeline — the answer to "where did that news go?"."""

    FETCH_FAILED = "fetch_failed"
    TOO_SHORT = "too_short"
    NOT_ARTICLE = "not_article"
    NO_DATE = "no_date"
    OUT_OF_WINDOW = "out_of_window"
    NO_TITLE = "no_title"


class ArticleOrigin(StrEnum):
    """Which discovery step produced the link."""

    LISTING = "listing"  # a card on a confirmed listing page
    LINK = "link"  # a link found on the home page or a listing page
