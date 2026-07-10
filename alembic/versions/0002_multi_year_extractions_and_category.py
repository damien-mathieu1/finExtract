"""multi-year extractions and line item category

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-02

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("uq_extractions_source_reference", "extractions", type_="unique")
    op.create_unique_constraint(
        "uq_extractions_source_reference_fiscal_year_period_label",
        "extractions",
        ["source_reference", "fiscal_year", "period_label"],
    )

    op.add_column(
        "line_items",
        sa.Column("category", sa.String(30), nullable=False, server_default="income_statement"),
    )
    op.alter_column("line_items", "category", server_default=None)


def downgrade() -> None:
    op.drop_column("line_items", "category")
    op.drop_constraint(
        "uq_extractions_source_reference_fiscal_year_period_label", "extractions", type_="unique"
    )
    op.create_unique_constraint(
        "uq_extractions_source_reference", "extractions", ["source_reference"]
    )
