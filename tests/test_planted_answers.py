"""Every planted problem is found, counted and handled as the answer key says."""
import json

from conftest import RAW, one

KEY = json.loads((RAW / "answer_key.json").read_text(encoding="utf-8"))
AS_OF = KEY["as_of"]


def test_rejections_by_reason(con):
    got = dict(con.execute("select reason_code, count(*) from gold.rpt_rejections group by 1").fetchall())
    assert got == KEY["rejections"]


def test_flags(con):
    q = dict(con.execute("select reason_code, affected from gold.rpt_quality_summary").fetchall())
    assert q["NO_HISTORY"] == KEY["no_history_workers"]
    assert q["MISSING_BRANCH"] == KEY["missing_branch_rows"]
    assert q["FUTURE_START"] >= KEY["future_starters"]
    assert one(con, "select exact_duplicate_rows from gold.rpt_quality_summary limit 1")[0] == KEY["exact_duplicate_rows"]


def test_headcount_matches_ground_truth(con):
    assert one(con, f"select count(*) from gold.fct_worker_month where month_end = date '{AS_OF}'")[0] == KEY["headcount_as_of"]
    by_emp = dict(con.execute(f"select employer_code, count(*) from gold.fct_worker_month where month_end = date '{AS_OF}' group by 1").fetchall())
    assert by_emp == KEY["headcount_by_employer"]


def test_continuous_service_start_for_every_worker(con):
    got = dict(con.execute(f"""select w.source_system || ':' || w.worker_id, cast(f.continuous_service_start as varchar)
                               from gold.fct_worker_month f join gold.dim_worker w using (worker_key)
                               where f.month_end = date '{AS_OF}' and f.has_seniority_evidence""").fetchall())
    assert got == KEY["continuous_service_start"]


def test_insufficient_evidence_is_explicit(con):
    n = one(con, f"select count(*) from gold.fct_worker_month where month_end = date '{AS_OF}' and tenure_band = '6. Insufficient evidence'")[0]
    assert n == KEY["seniority_evidence_insufficient"]


def test_ids_reused_across_systems_stay_separate(con):
    n = one(con, "select count(*) from (select worker_id from gold.dim_worker group by 1 having count(distinct source_system) = 2)")[0]
    assert n == KEY["id_collisions"]


def test_extracts_compared_field_by_field(con):
    r = one(con, "select rows_a, rows_b, job_family_differs, only_in_a + only_in_b from gold.rpt_extract_comparison")
    assert r[0] == r[1] and r[2] == KEY["extract_differences"] and r[3] == 0


def test_branch_region_is_as_of(con):
    rc = KEY["region_change"]
    before = one(con, f"""select any_value(region) from gold.fct_worker_month
                         where branch_code = '{rc["branch"]}' and month_end = last_day(date '{rc["on"]}' - interval 1 day)""")[0]
    after = one(con, f"select any_value(region) from gold.fct_worker_month where branch_code = '{rc['branch']}' and month_end = last_day(date '{rc['on']}')")[0]
    assert after == rc["to"] and before not in (None, rc["to"])


def test_closed_branch_has_no_workers_after_closing(con):
    cb = KEY["closed_branch"]
    assert one(con, f"select count(*) from gold.fct_worker_month where branch_code = '{cb['branch']}' and month_end > date '{cb['on']}'")[0] == 0
