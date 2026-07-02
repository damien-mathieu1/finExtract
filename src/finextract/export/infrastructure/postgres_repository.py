from __future__ import annotations

from sqlalchemy import Float, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from finextract.mapping.domain.models import FinancialStatement


class Base(DeclarativeBase):
    pass


class LineItemRow(Base):
    __tablename__ = "line_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String(255))
    fiscal_year: Mapped[int] = mapped_column(Integer)
    period_label: Mapped[str] = mapped_column(String(50))
    currency: Mapped[str] = mapped_column(String(3))
    accounting_standard: Mapped[str] = mapped_column(String(50))
    field_name: Mapped[str] = mapped_column(String(100))
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    original_label: Mapped[str] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(10))
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)


class PostgresExporter:
    """ExportPort implementation persisting a FinancialStatement to Postgres.

    Returns an empty bytes payload (nothing to download) since the Load
    target here is the database, not a file — callers should check the
    export format before expecting file bytes back.
    """

    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url)
        self._session_factory: sessionmaker[Session] = sessionmaker(bind=self._engine)

    def export(self, statement: FinancialStatement) -> bytes:
        with self._session_factory() as session:
            rows = [
                LineItemRow(
                    company_name=statement.company_name,
                    fiscal_year=statement.fiscal_period.fiscal_year,
                    period_label=statement.fiscal_period.period_label,
                    currency=statement.currency.value,
                    accounting_standard=statement.accounting_standard.value,
                    field_name=li.field_name,
                    value=li.value,
                    original_label=li.original_label,
                    source=li.source,
                    page_number=li.page_number,
                    confidence_score=li.confidence_score,
                )
                for li in statement.line_items
            ]
            session.add_all(rows)
            session.commit()
        return b""
