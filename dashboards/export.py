"""Collect the aggregates the dashboard pages show into one JSON document. Counts only: no worker keys, IDs or rows.

Usage: python dashboards/export.py --db warehouse/workforce.duckdb --out dashboards/site/data.json
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def rows(con, sql: str) -> list[dict]:
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    out = []
    for r in cur.fetchall():
        rec = {}
        for k, v in zip(cols, r):
            if isinstance(v, (datetime, date)):
                v = v.isoformat()[:10]
            elif isinstance(v, float):
                v = round(v, 6)
            elif v is not None and not isinstance(v, (int, str, bool)):
                v = float(v)
            rec[k] = v
        out.append(rec)
    return out


def collect(con) -> dict:
    d: dict = {}
    d["as_of"] = con.execute("select max(month_end) from gold.fct_worker_month").fetchone()[0].isoformat()
    d["bridge"] = rows(con, "select * from gold.rpt_headcount_bridge order by step_no")
    d["naive_emp"] = rows(con, """select n.*, e.employer_name from gold.rpt_headcount_naive_by_employer n
                                  left join gold.dim_employer e using (employer_code) order by employer_code""")
    d["monthly"] = rows(con, "select * from gold.rpt_headcount_monthly order by month_end, employer_code")
    d["asof"] = rows(con, """select employer_code, any_value(employer_name) as employer_name, sum(workers) as workers
                             from gold.rpt_headcount_asof group by 1 order by 1""")
    d["region"] = rows(con, "select region, sum(workers) as workers from gold.rpt_headcount_asof group by 1 order by 2 desc")
    # Employer x tenure band, suppressed below the minimum cell size before export.
    d["cells"] = rows(con, """select employer_code, tenure_band, case when sum(workers) >= 5 then sum(workers) end as workers
                              from gold.rpt_headcount_asof group by 1, 2 order by 1, 2""")
    d["bands"] = rows(con, "select * from gold.rpt_tenure_bands order by tenure_band")
    d["recon"] = rows(con, "select * from gold.rpt_reconciliation")
    d["quality"] = rows(con, "select * exclude (raw_rows, deduplicated_rows, exact_duplicate_rows) from gold.rpt_quality_summary")
    d["totals"] = rows(con, "select raw_rows, deduplicated_rows, exact_duplicate_rows from gold.rpt_quality_summary limit 1")[0]
    d["by_source"] = rows(con, "select * from gold.rpt_rejections_by_source order by source_system, reason_code")
    d["formats"] = rows(con, "select * from gold.rpt_date_formats order by source_system, field, format")
    d["missing_branch"] = rows(con, f"""select employer_code, count(*) filter (where is_missing_branch) as missing, count(*) as workers
                                         from gold.fct_worker_month where month_end = date '{d["as_of"]}' group by 1 order by 1""")
    d["fixtures"] = rows(con, "select * from gold.rpt_tenure_fixtures order by case_id")
    d["extracts"] = rows(con, "select * from gold.rpt_extract_comparison")[0]
    d["workers"] = rows(con, """select count(*) as in_master, count(*) filter (where has_no_history) as no_history,
                                count(*) filter (where not has_seniority_evidence and not has_no_history) as with_rejected_rows
                                from gold.dim_worker""")[0]
    return d


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "warehouse" / "workforce.duckdb"))
    ap.add_argument("--out", default=str(HERE / "site" / "data.json"))
    ap.add_argument("--dbt-results", default=str(ROOT / "dbt" / "target" / "run_results.json"))
    a = ap.parse_args()
    with duckdb.connect(a.db, read_only=True) as con:
        data = collect(con)
    rr = Path(a.dbt_results)
    if rr.exists():
        results = json.loads(rr.read_text(encoding="utf-8"))["results"]
        data["dbt"] = {"nodes": len(results), "passed": sum(r["status"] in ("pass", "success") for r in results),
                       "tests": sum(r["unique_id"].startswith("test.") for r in results)}
    Path(a.out).write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
