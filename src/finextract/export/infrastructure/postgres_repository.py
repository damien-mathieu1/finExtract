from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, create_engine, func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

from finextract.export.domain.models import ExtractionSummary
from finextract.mapping.domain.models import FinancialStatement, LineItem
from finextract.shared_kernel.value_objects import Currency, FiscalPeriod, ReportingStandard


class Base(DeclarativeBase):
    pass


class ExtractionRow(Base):
    __tablename__ = "extractions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String(255))
    fiscal_year: Mapped[int] = mapped_column(Integer)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    period_label: Mapped[str] = mapped_column(String(50))
    currency: Mapped[str] = mapped_column(String(3))
    accounting_standard: Mapped[str] = mapped_column(String(50))
    source_reference: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    extracted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    line_items: Mapped[list[LineItemRow]] = relationship(
        back_populates="extraction", cascade="all, delete-orphan"
    )


class LineItemRow(Base):
    __tablename__ = "line_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    extraction_id: Mapped[int] = mapped_column(ForeignKey("extractions.id", ondelete="CASCADE"))
    field_name: Mapped[str] = mapped_column(String(100))
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    original_label: Mapped[str] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(10))
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    extraction: Mapped[ExtractionRow] = relationship(back_populates="line_items")


class PostgresExporter:
    """Persists and queries FinancialStatements against Postgres.

    Implements ExportPort (export -> bytes, for parity with the CSV/Excel
    exporters even though the "file" is empty since the load target is the
    database), ExtractionPersisterPort (the actual persistence write, keyed
    by source_reference so re-extracting a filing upserts instead of
    duplicating history), and ExtractionQueryPort (list/detail reads for the
    "what's already been extracted?" frontend flow).
    """

    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url)
        self._session_factory: sessionmaker[Session] = sessionmaker(bind=self._engine)

    def export(self, statement: FinancialStatement) -> bytes:
        return b""

    def persist(self, statement: FinancialStatement, source_reference: str) -> None:
        with self._session_factory() as session:
            existing = (
                session.query(ExtractionRow)
                .filter(ExtractionRow.source_reference == source_reference)
                .one_or_none()
            )
            if existing is None:
                existing = ExtractionRow(source_reference=source_reference)
                session.add(existing)
            else:
                existing.line_items.clear()
                existing.extracted_at = func.now()

            existing.company_name = statement.company_name
            existing.fiscal_year = statement.fiscal_period.fiscal_year
            existing.period_start = statement.fiscal_period.start_date
            existing.period_end = statement.fiscal_period.end_date
            existing.period_label = statement.fiscal_period.period_label
            existing.currency = statement.currency.value
            existing.accounting_standard = statement.accounting_standard.value
            existing.line_items = [
                LineItemRow(
                    field_name=li.field_name,
                    value=li.value,
                    original_label=li.original_label,
                    source=li.source,
                    page_number=li.page_number,
                    confidence_score=li.confidence_score,
                )
                for li in statement.line_items
            ]
            session.commit()

    def list_extractions(
        self, *, company_identifier: str | None = None, source_reference: str | None = None
    ) -> list[ExtractionSummary]:
        with self._session_factory() as session:
            query = session.query(ExtractionRow)
            if source_reference is not None:
                query = query.filter(ExtractionRow.source_reference == source_reference)
            if company_identifier is not None:
                query = query.filter(
                    (ExtractionRow.company_name.ilike(f"%{company_identifier}%"))
                    | (ExtractionRow.source_reference.ilike(f"%{company_identifier}%"))
                )
            rows = query.order_by(ExtractionRow.extracted_at.desc()).all()
            return [
                ExtractionSummary(
                    id=row.id,
                    company_name=row.company_name,
                    fiscal_year=row.fiscal_year,
                    period_label=row.period_label,
                    currency=row.currency,
                    accounting_standard=row.accounting_standard,
                    source_reference=row.source_reference,
                    extracted_at=row.extracted_at,
                )
                for row in rows
            ]

    def get_extraction(self, extraction_id: int) -> FinancialStatement | None:
        with self._session_factory() as session:
            row = session.get(ExtractionRow, extraction_id)
            if row is None:
                return None
            return FinancialStatement(
                company_name=row.company_name,
                fiscal_period=FiscalPeriod(
                    fiscal_year=row.fiscal_year,
                    start_date=row.period_start,
                    end_date=row.period_end,
                    period_label=row.period_label,
                ),
                currency=Currency(row.currency),
                accounting_standard=ReportingStandard(row.accounting_standard),
                line_items=[
                    LineItem(
                        field_name=li.field_name,
                        value=li.value,
                        original_label=li.original_label,
                        source=li.source,
                        page_number=li.page_number,
                        confidence_score=li.confidence_score,
                    )
                    for li in row.line_items
                ],
            )
