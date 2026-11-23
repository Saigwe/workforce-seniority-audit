"""Rules that hold whatever the data: tenure arithmetic, reconciliation, one placement at a time."""
from datetime import date

import pytest

from conftest import one


def tenure(start: date, as_of: date):
    """Python twin of the dbt macro, for property checks."""
    if start > as_of:
        return None
    import calendar
    m = (as_of.year - start.year) * 12 + as_of.month - start.month
    eom = as_of.day == calendar.monthrange(as_of.year, as_of.month)[1]
    return m - (1 if as_of.day < start.day and not eom else 0)


def test_fixtures_agree_with_python_twin(con):
    for start, as_of, expected, computed in con.execute("select start_date, as_of_date, expected_months, computed_months from gold.rpt_tenure_fixtures").fetchall():
        assert computed == expected == tenure(start, as_of)


@pytest.mark.parametrize("start,as_of,expected", [
    (date(2024, 2, 29), date(2025, 2, 28), 12),
    (date(2026, 1, 31), date(2026, 2, 28), 1),
    (date(2026, 1, 31), date(2026, 3, 30), 1),
    (date(2026, 1, 31), date(2026, 3, 31), 2),
])
def test_month_end_and_leap_year(start, as_of, expected):
    assert tenure(start, as_of) == expected


def test_tenure_in_warehouse_matches_python_twin(con):
    rows = con.execute("select continuous_service_start, month_end, tenure_months from gold.fct_worker_month where has_seniority_evidence using sample 3000 rows (reservoir, 7)").fetchall()
    assert rows and all(tenure(s, m) == t for s, m, t in rows)


def test_headcount_reconciles_under_every_filter(con):
    vals = {r[0] for r in con.execute("select workers from gold.rpt_reconciliation").fetchall()}
    assert len(vals) == 1


def test_naive_count_differs_and_bridge_explains_it(con):
    naive, total = one(con, "select max(running_total) filter (where step_no = 1), max(running_total) filter (where step_no = 7) from gold.rpt_headcount_bridge")
    assert naive != total
    assert one(con, "select sum(change) from gold.rpt_headcount_bridge where step_no < 7")[0] == total


def test_every_raw_row_is_valid_or_rejected_once(con):
    raw, dedup, dupes = one(con, "select raw_rows, deduplicated_rows, exact_duplicate_rows from gold.rpt_quality_summary limit 1")
    valid = one(con, "select count(*) from gold.fct_placement")[0]
    rejected = one(con, "select count(*) from gold.rpt_rejections")[0]
    assert raw == dedup + dupes and dedup == valid + rejected
    assert one(con, "select count(*) - count(distinct record_id) from gold.rpt_rejections")[0] == 0


def test_open_ended_spellings_all_mean_open(con):
    fmts = dict(con.execute("select end_format, count(*) from silver.int_placement_checks group by 1").fetchall())
    assert fmts.get("open", 0) > 0
    assert one(con, "select count(*) from silver.int_placement_checks where is_open_ended and end_date is not null")[0] == 0


def test_published_marts_hold_no_worker_detail(con):
    cols = con.execute("""select table_name, column_name from information_schema.columns where table_schema = 'gold'
                          and table_name like 'rpt_%' and table_name <> 'rpt_rejections' and column_name in ('worker_key', 'worker_id', 'record_id')""").fetchall()
    assert cols == []
