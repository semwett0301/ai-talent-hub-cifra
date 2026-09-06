"""npa: persist tracking state and immutable bill versions

Revision ID: 0013_npa_tracking_versions
Revises: 0013_rss_link_table
Create Date: 2026-09-06

Generated with Alembic autogenerate, then reviewed to remove unrelated legacy
nullability drift on source timestamps and to follow repository revision naming.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013_npa_tracking_versions"
down_revision: str | None = "0013_rss_link_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "npa_version",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("npa_id", sa.Uuid(), nullable=False),
        sa.Column("stage", sa.String(length=256), nullable=False),
        sa.Column("stage_code", sa.String(length=32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("document_url", sa.String(length=2048), nullable=False),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "article_changes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["npa_id"], ["npa.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_npa_version_npa_id", "npa_version", ["npa_id"], unique=False)
    _add_current_state_columns()


def downgrade() -> None:
    for column in (
        "updated_at",
        "article_changes",
        "summary",
        "tracking_status",
        "last_checked_at",
        "source_updated_at",
        "document_url",
        "stage_code",
        "stage",
        "bill_number",
    ):
        op.drop_column("npa", column)
    op.drop_index("ix_npa_version_npa_id", table_name="npa_version")
    op.drop_table("npa_version")


def _add_current_state_columns() -> None:
    op.add_column("npa", sa.Column("bill_number", sa.String(length=64), nullable=True))
    op.add_column("npa", sa.Column("stage", sa.String(length=256), nullable=True))
    op.add_column("npa", sa.Column("stage_code", sa.String(length=32), nullable=True))
    op.add_column("npa", sa.Column("document_url", sa.String(length=2048), nullable=True))
    op.add_column("npa", sa.Column("source_updated_at", sa.DateTime(timezone=True)))
    op.add_column("npa", sa.Column("last_checked_at", sa.DateTime(timezone=True)))
    op.add_column("npa", _tracking_status_column())
    op.add_column("npa", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column(
        "npa",
        sa.Column("article_changes", postgresql.JSONB(), server_default="[]", nullable=False),
    )
    op.add_column(
        "npa",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def _tracking_status_column() -> sa.Column:
    status_type = sa.Enum(
        "tracking",
        "published",
        "unsupported",
        name="npa_tracking_status",
        native_enum=False,
        length=16,
    )
    return sa.Column("tracking_status", status_type, server_default="unsupported", nullable=False)
