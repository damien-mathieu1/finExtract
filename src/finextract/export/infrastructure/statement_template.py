from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources

from finextract.shared_kernel.value_objects import StatementCategory

_SHEET_TO_CATEGORY: dict[str, StatementCategory] = {
    "PL": StatementCategory.INCOME_STATEMENT,
    "BS": StatementCategory.BALANCE_SHEET,
    "CS": StatementCategory.CASH_FLOW,
}


@dataclass(frozen=True, slots=True)
class TemplateRow:
    """One canonical row in the Bloomberg-style statement template: a
    standard field expected in a given statement, in the fixed display
    order/label/code the original xlsx uses - independent of whether any
    given export actually has data for it."""

    category: StatementCategory
    standard_field: str
    bloomberg_code: str
    label: str


@lru_cache(maxsize=1)
def load_statement_template() -> tuple[TemplateRow, ...]:
    """Loads the canonical, ordered row template from the packaged
    statement_template.csv (a copy of docs/xbrl_taxonomy_correspondence.csv).
    Row order in the CSV is preserved as export row order. Some rows have no
    corresponding data in any given export (rollups, disclosure-only items
    with no direct XBRL concept) - they're still included and simply render
    blank for every period."""
    csv_text = (
        resources.files("finextract.export.infrastructure")
        .joinpath("data", "statement_template.csv")
        .read_text(encoding="utf-8")
    )
    reader = csv.DictReader(csv_text.splitlines())
    return tuple(
        TemplateRow(
            category=_SHEET_TO_CATEGORY[row["statement"]],
            standard_field=row["standard_field"],
            bloomberg_code=row["bloomberg_field"],
            label=row["label"],
        )
        for row in reader
    )
