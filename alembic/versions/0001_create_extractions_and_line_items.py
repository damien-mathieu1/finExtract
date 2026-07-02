"""create extractions and line_items

Revision ID: 0001
Revises:
Create Date: 2026-07-02

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "extractions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("period_label", sa.String(50), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("accounting_standard", sa.String(50), nullable=False),
        sa.Column("source_reference", sa.String(500), nullable=False),
        sa.Column("extracted_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint(
        "uq_extractions_source_reference", "extractions", ["source_reference"]
    )
    op.create_index(
        "ix_extractions_company_fiscal_year", "extractions", ["company_name", "fiscal_year"]
    )

    op.create_table(
        "line_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "extraction_id",
            sa.Integer(),
            sa.ForeignKey("extractions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("original_label", sa.String(255), nullable=False),
        sa.Column("source", sa.String(10), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
    )
    op.create_index("ix_line_items_extraction_id", "line_items", ["extraction_id"])


def downgrade() -> None:
    op.drop_table("line_items")
    op.drop_table("extractions")
