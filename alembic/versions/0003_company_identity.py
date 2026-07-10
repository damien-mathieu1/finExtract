"""company identity (cik/ticker) on extractions

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-10

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("extractions", sa.Column("cik", sa.String(20), nullable=True))
    op.add_column("extractions", sa.Column("ticker", sa.String(20), nullable=True))
    op.create_index("ix_extractions_cik", "extractions", ["cik"])


def downgrade() -> None:
    op.drop_index("ix_extractions_cik", table_name="extractions")
    op.drop_column("extractions", "ticker")
    op.drop_column("extractions", "cik")
