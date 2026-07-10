from finextract.export.infrastructure.statement_template import load_statement_template
from finextract.shared_kernel.value_objects import StatementCategory


def test_load_statement_template_covers_all_categories() -> None:
    rows = load_statement_template()

    assert len(rows) > 0
    categories = {row.category for row in rows}
    assert categories == {
        StatementCategory.INCOME_STATEMENT,
        StatementCategory.BALANCE_SHEET,
        StatementCategory.CASH_FLOW,
    }


def test_load_statement_template_rows_have_code_and_standard_field() -> None:
    rows = load_statement_template()

    for row in rows:
        assert row.standard_field
        assert row.bloomberg_code
        assert row.label


def test_load_statement_template_preserves_known_row() -> None:
    rows = load_statement_template()

    revenue_rows = [r for r in rows if r.standard_field == "revenue"]
    assert len(revenue_rows) == 1
    assert revenue_rows[0].category == StatementCategory.INCOME_STATEMENT
    assert revenue_rows[0].bloomberg_code == "SALES_REV_TURN"
