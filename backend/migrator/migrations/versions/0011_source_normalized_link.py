"""source: add normalized_link, unique per address

Revision ID: 0011_source_normalized_link
Revises: 0010_news_source_id
Create Date: 2026-09-06

Adds `normalized_link` — the canonical spelling of `link`, so two rows that differ
only by case, `www.`, a trailing slash or tracking params cannot both exist. The API
maps the resulting IntegrityError to a 409.

The backfill mirrors `source_service.domain.urls.source_identity`, deliberately
copied rather than imported: the migrator depends only on `common`, and a revision
must keep applying the same way even if that function later changes.
"""

from collections.abc import Sequence
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import sqlalchemy as sa
from alembic import op

revision: str = "0011_source_normalized_link"
down_revision: str | None = "0010_news_source_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UNIQUE_CONSTRAINT = "uq_source_normalized_link"
HTTP_SCHEMES = frozenset({"http", "https"})
WWW_PREFIX = "www."
TRACKING_PARAMS = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "gclid",
        "fbclid",
        "yclid",
        "_ga",
        "ref",
        "source",
    }
)

source_table = sa.table(
    "source",
    sa.column("id", sa.Uuid),
    sa.column("link", sa.String),
    sa.column("normalized_link", sa.String),
)


def _source_identity(link: str) -> str:
    parsed = urlparse(link)
    if parsed.scheme.lower() not in HTTP_SCHEMES:
        return link.strip().lower()

    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in TRACKING_PARAMS
    ]
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")

    host = parsed.netloc.lower().removeprefix(WWW_PREFIX)
    return urlunparse((parsed.scheme.lower(), host, path, "", urlencode(query), ""))


def upgrade() -> None:
    op.add_column("source", sa.Column("normalized_link", sa.String(length=255), nullable=True))

    connection = op.get_bind()
    rows = connection.execute(sa.select(source_table.c.id, source_table.c.link)).fetchall()
    for source_id, link in rows:
        connection.execute(
            source_table.update()
            .where(source_table.c.id == source_id)
            .values(normalized_link=_source_identity(link))
        )

    op.alter_column("source", "normalized_link", nullable=False)
    op.create_unique_constraint(UNIQUE_CONSTRAINT, "source", ["normalized_link"])


def downgrade() -> None:
    op.drop_constraint(UNIQUE_CONSTRAINT, "source", type_="unique")
    op.drop_column("source", "normalized_link")
