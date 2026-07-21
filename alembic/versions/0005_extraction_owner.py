"""per-user ownership on extractions

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-21

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Pre-auth rows have no owner; wiping them lets owner_id be NOT NULL
    # without a placeholder default.
    op.execute("DELETE FROM line_items")
    op.execute("DELETE FROM extractions")
    op.add_column("extractions", sa.Column("owner_id", sa.String(64), nullable=False))
    op.create_index("ix_extractions_owner_id", "extractions", ["owner_id"])
    op.drop_constraint(
        "uq_extractions_source_reference_fiscal_year_period_label",
        "extractions",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_extractions_owner_source_fy_period",
        "extractions",
        ["owner_id", "source_reference", "fiscal_year", "period_label"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_extractions_owner_source_fy_period", "extractions", type_="unique")
    op.create_unique_constraint(
        "uq_extractions_source_reference_fiscal_year_period_label",
        "extractions",
        ["source_reference", "fiscal_year", "period_label"],
    )
    op.drop_index("ix_extractions_owner_id", table_name="extractions")
    op.drop_column("extractions", "owner_id")
