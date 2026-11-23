"""Synthetic worker master data and placement history for a fictional payroll services company.

Two payroll systems deliver worker extracts and placement history with the problems real HR extracts have: mixed date
formats, malformed and impossible dates, open-ended periods spelt three ways, duplicate rows, conflicting employer
assignments, rehires, gaps, missing branches, unknown employers, workers with no history and history with no worker.
Every problem is planted deliberately and recorded in answer_key.json, with the headcount the rules should produce.

No real person, employer or record is represented. Worker IDs are generated numbers; there are no names, birth dates
or national identifiers anywhere.

Usage: python generator/simulate.py --out data/raw [--seed 31]
"""
from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

AS_OF = date(2026, 10, 31)
FIRST_HIRE = date(2010, 1, 4)
BRIDGE_DAYS = 31            # gaps up to this many days keep continuous service with the same employer
EXTRACTED_AT = "2026-11-01 06:00:00"

EMPLOYERS = [
    ("EMP-01", "Harbourline Logistics", "Logistics"), ("EMP-02", "Copperfield Foods", "Food production"),
    ("EMP-03", "Northgate Retail Group", "Retail"), ("EMP-04", "Alder Health Services", "Healthcare"),
    ("EMP-05", "Brightmoor Engineering", "Manufacturing"), ("EMP-06", "Quayside Hospitality", "Hospitality"),
    ("EMP-07", "Fernhill Facilities", "Facilities"), ("EMP-08", "Lumen Contact Centres", "Services"),
    ("EMP-09", "Stonebridge Construction", "Construction"), ("EMP-10", "Westmere Cleaning Co.", "Facilities"),
]
REGIONS = ["North", "South", "East", "West", "Central"]
JOB_FAMILIES = ["Operations", "Warehouse", "Care", "Production", "Front of house", "Cleaning", "Office", "Trades"]
CONTRACTS = ["permanent", "fixed-term", "temporary"]
BAD_DATES = ["31/02/2024", "2023-13-01", "N/A", "00/00/0000", "2025-02-30"]
REGION_CHANGE = ("BR-017", date(2025, 7, 1), "Central")    # branch moves region: dim_branch is slowly changing
CLOSED_BRANCH = ("BR-030", date(2025, 12, 31))             # branch closes; its workers transfer to a sibling


def fmt_date(d: date | None, system: str, rng: np.random.Generator) -> str:
    """Format a date the way the source system does, with occasional other formats."""
    if d is None:
        return {"PAY-N": "", "PAY-S": "31/12/9999"}[system] if rng.random() < 0.85 else "9999-12-31"
    u = rng.random()
    if u < 0.08:
        return d.strftime("%Y%m%d")
    if u < 0.10:
        return str((d - date(1899, 12, 30)).days)          # spreadsheet serial number
    return d.isoformat() if system == "PAY-N" else d.strftime("%d/%m/%Y")


def build_branches(rng):
    rows, by_emp, n = [], {}, 0
    for code, _, _ in EMPLOYERS:
        k = int(rng.integers(3, 6))
        by_emp[code] = []
        for _ in range(k):
            n += 1
            b = f"BR-{n:03d}"
            region = REGIONS[int(rng.integers(len(REGIONS)))]
            opened = FIRST_HIRE - timedelta(days=int(rng.integers(0, 900)))
            by_emp[code].append(b)
            if b == REGION_CHANGE[0]:
                rows.append((b, code, f"{code[-2:]}-{n:03d} depot", region if region != REGION_CHANGE[2] else "East", opened, REGION_CHANGE[1] - timedelta(days=1)))
                rows.append((b, code, f"{code[-2:]}-{n:03d} depot", REGION_CHANGE[2], REGION_CHANGE[1], None))
            elif b == CLOSED_BRANCH[0]:
                rows.append((b, code, f"{code[-2:]}-{n:03d} depot", region, opened, CLOSED_BRANCH[1]))
            else:
                rows.append((b, code, f"{code[-2:]}-{n:03d} depot", region, opened, None))
    return rows, by_emp


def worker_history(rng, wid, system, by_emp, hire: date):
    """True placements of one worker: list of dicts with real dates (end None = open)."""
    out = []
    emp = EMPLOYERS[int(rng.integers(len(EMPLOYERS)))][0]
    start = hire
    while True:
        branch = by_emp[emp][int(rng.integers(len(by_emp[emp])))]
        if branch == CLOSED_BRANCH[0] and start > CLOSED_BRANCH[1]:
            branch = by_emp[emp][0]
        dur = int(rng.exponential(1000)) + 30
        end = start + timedelta(days=dur)
        if branch == CLOSED_BRANCH[0] and end > CLOSED_BRANCH[1] >= start:
            end = CLOSED_BRANCH[1]
        contract = CONTRACTS[int(rng.choice(3, p=[0.7, 0.2, 0.1]))]
        if end > AS_OF:
            # fixed-term contracts carry a known end date after the as-of date; others are open
            out.append(dict(employer=emp, branch=branch, start=start, end=end if contract == "fixed-term" else None, contract=contract))
            return out
        out.append(dict(employer=emp, branch=branch, start=start, end=end, contract=contract))
        u = rng.random()
        if branch == CLOSED_BRANCH[0] and end == CLOSED_BRANCH[1]:
            start = end + timedelta(days=1)                   # moved to a sibling branch
            continue
        if u < 0.30:                                          # leaves
            if rng.random() < 0.25:                            # rehired later
                start = end + timedelta(days=int(rng.integers(90, 1500)))
                if start > AS_OF:
                    return out
                if rng.random() < 0.5:
                    emp = EMPLOYERS[int(rng.integers(len(EMPLOYERS)))][0]
                continue
            return out
        if u < 0.80:
            start = end + timedelta(days=1)                   # transfer, no gap
        elif u < 0.90:
            start = end + timedelta(days=int(rng.integers(5, BRIDGE_DAYS + 1)))   # short gap: bridged
        else:
            start = end + timedelta(days=int(rng.integers(45, 400)))             # long gap: service restarts
            if start > AS_OF:
                return out
            if rng.random() < 0.4:
                emp = EMPLOYERS[int(rng.integers(len(EMPLOYERS)))][0]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/raw")
    ap.add_argument("--seed", type=int, default=31)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    branch_rows, by_emp = build_branches(rng)

    # Workers: two payroll systems with overlapping numeric ID ranges, so 15 IDs exist in both as different people.
    workers = [("PAY-N", str(100001 + i)) for i in range(1800)] + [("PAY-S", str(101786 + i)) for i in range(1400)]
    span = (AS_OF - FIRST_HIRE).days
    hires = {}
    for s, w in workers:
        hires[(s, w)] = FIRST_HIRE + timedelta(days=int(span * rng.power(1.8)))
    # month-end and leap-day starters, so tenure edge cases are exercised
    leap = [date(2016, 2, 29), date(2020, 2, 29), date(2024, 2, 29)]
    for i, key in enumerate(workers[10:22]):
        hires[key] = leap[i % 3]
    for i, key in enumerate(workers[30:54]):
        m = date(2012 + i % 14, 1 + (i * 5) % 12, 28)
        nxt = (m.replace(day=1) + timedelta(days=32)).replace(day=1)
        hires[key] = nxt - timedelta(days=1)                   # last day of the month

    true = {}
    for key in workers:
        true[key] = worker_history(rng, key[1], key[0], by_emp, hires[key])

    # The 35 workers with no history and 18 future starters are separate, added below.
    order = [k for k in workers if k not in set(workers[10:54])]
    rng.shuffle(order)
    pools = iter(order)
    pick = lambda n, cond=lambda k: True: [k for k in (next(pools) for _ in range(5 * n)) if cond(k)][:n]
    active = lambda k: true[k][-1]["end"] is None or true[k][-1]["end"] > AS_OF
    multi = lambda k: len(true[k]) >= 2

    unparseable = pick(25, active)
    end_before_start = pick(12, multi)
    unknown_emp = pick(6, multi)
    dup_conflict = pick(8, multi)
    overlap = pick(20, active)
    exact_dupes = pick(40)
    missing_branch = pick(70, active)

    rows = []
    def emit(sys_, wid, p, start_s=None, end_s=None, employer=None, branch=None):
        rows.append(dict(source_system=sys_, worker_id=wid, employer_code=employer or p["employer"],
                         branch_code=p["branch"] if branch is None else branch,
                         start_date=start_s if start_s is not None else fmt_date(p["start"], sys_, rng),
                         end_date=end_s if end_s is not None else fmt_date(p["end"], sys_, rng),
                         contract_type=p["contract"], fte=str(rng.choice(["1.0", "1.0", "1.0", "0.8", "0.6", "0.5"]))))

    reject = {}            # (system, worker) -> reasons, for the answer key
    for key in workers:
        s, w = key
        hist = true[key]
        for i, p in enumerate(hist):
            last, closed_mid = i == len(hist) - 1, i == 0 and len(hist) >= 2
            if key in unparseable and last:
                emit(s, w, p, start_s=BAD_DATES[len(reject) % len(BAD_DATES)]); reject.setdefault(key, []).append("UNPARSEABLE_DATE"); continue
            if key in end_before_start and closed_mid:
                emit(s, w, p, start_s=fmt_date(p["end"], s, rng), end_s=fmt_date(p["start"], s, rng)); reject.setdefault(key, []).append("END_BEFORE_START"); continue
            if key in unknown_emp and closed_mid:
                emit(s, w, p, employer="EMP-99"); reject.setdefault(key, []).append("UNKNOWN_EMPLOYER"); continue
            if key in dup_conflict and closed_mid:
                emit(s, w, p)
                emit(s, w, p, end_s=fmt_date(p["end"] + timedelta(days=40), s, rng)); reject.setdefault(key, []).append("DUPLICATE_KEY_CONFLICT"); continue
            if key in missing_branch and last:
                emit(s, w, p, branch=""); continue
            emit(s, w, p)
            if key in exact_dupes and last:
                rows.append(dict(rows[-1]))
            if key in overlap and last:
                other = next(e for e, _, _ in EMPLOYERS if e != p["employer"])
                q = dict(employer=other, branch=by_emp[other][0], start=max(p["start"], AS_OF - timedelta(days=200)) + timedelta(days=17), end=None, contract="temporary")
                emit(s, w, q); reject.setdefault(key, []).append("OVERLAP_CONFLICT")

    # Starters signed for November and December: valid, but not employed at the as-of date.
    future = []
    for i in range(18):
        key = ("PAY-N" if i % 2 else "PAY-S", str(104001 + i))
        emp = EMPLOYERS[i % len(EMPLOYERS)][0]
        p = dict(employer=emp, branch=by_emp[emp][0], start=AS_OF + timedelta(days=2 + 3 * i), end=None, contract="permanent")
        true[key] = [p]; future.append(key)
        emit(key[0], key[1], p)
    # History rows whose worker is in neither master extract.
    orphans = [("PAY-S", str(109001 + i)) for i in range(5)]
    for key in orphans:
        emp = EMPLOYERS[0][0]
        emit(key[0], key[1], dict(employer=emp, branch=by_emp[emp][0], start=date(2025, 3, 3), end=None, contract="temporary"))
    no_history = [("PAY-N" if i % 3 else "PAY-S", str(108001 + i)) for i in range(35)]

    hist_df = pd.DataFrame(rows)
    hist_df = hist_df.iloc[rng.permutation(len(hist_df))].reset_index(drop=True)
    hist_df.insert(0, "record_id", [f"H{i + 1:06d}" for i in range(len(hist_df))])
    hist_df["extracted_at"] = EXTRACTED_AT
    hist_df.to_parquet(out / "placement_history.parquet", index=False)

    # Worker master: two extracts with the same header and row count. They are not identical: four job families differ.
    master_keys = workers + future + no_history
    m = pd.DataFrame({
        "source_system": [k[0] for k in master_keys],
        "worker_id": [k[1] for k in master_keys],
        "job_family": [JOB_FAMILIES[int(rng.integers(len(JOB_FAMILIES)))] for _ in master_keys],
        "home_region": [REGIONS[int(rng.integers(len(REGIONS)))] for _ in master_keys],
        "record_created": [fmt_date(hires.get(k, AS_OF), k[0], rng) for k in master_keys],
    })
    m_a = m.copy(); m_a["extract_name"] = "worker_master_a"; m_a["extracted_at"] = "2026-11-01 05:58:00"
    m_b = m.copy(); m_b["extract_name"] = "worker_master_b"; m_b["extracted_at"] = "2026-11-01 06:04:00"
    changed = rng.choice(len(workers), 4, replace=False)
    for i in changed:
        cur = m_b.at[i, "job_family"]
        m_b.at[i, "job_family"] = JOB_FAMILIES[(JOB_FAMILIES.index(cur) + 1) % len(JOB_FAMILIES)]
    pd.concat([m_a, m_b]).to_parquet(out / "worker_master.parquet", index=False)

    pd.DataFrame([dict(employer_code=c, employer_name=n, sector=s) for c, n, s in EMPLOYERS]).to_parquet(out / "employers.parquet", index=False)
    pd.DataFrame([dict(branch_code=b, employer_code=e, branch_name=nm, region=r, valid_from=vf.isoformat(),
                       valid_to=vt.isoformat() if vt else "") for b, e, nm, r, vf, vt in branch_rows]).to_parquet(out / "branches.parquet", index=False)

    # Ground truth at the as-of date, computed from the true placements with the documented rules.
    rejected_workers = set(reject)
    def covers(p, d):
        return p["start"] <= d and (p["end"] is None or p["end"] >= d)
    headcount, by_emp_hc, seniority = 0, {}, {}
    for key in workers:
        hist = true[key]
        cur = [p for p in hist if covers(p, AS_OF)]
        if not cur:
            continue
        if key in overlap or (key in unparseable):
            continue                                   # the placement covering the as-of date is rejected
        p = cur[0]
        headcount += 1
        by_emp_hc[p["employer"]] = by_emp_hc.get(p["employer"], 0) + 1
        if key in rejected_workers:
            continue
        start = p["start"]
        for q in reversed([x for x in hist if x["start"] < p["start"]]):
            if q["employer"] == p["employer"] and (start - q["end"]).days <= BRIDGE_DAYS + 1:
                start = q["start"]
            else:
                break
        seniority[f"{key[0]}:{key[1]}"] = start.isoformat()

    key = dict(
        as_of=AS_OF.isoformat(), bridge_days=BRIDGE_DAYS,
        workers_in_master=len(master_keys), id_collisions=15,
        history_rows=len(hist_df), exact_duplicate_rows=len(exact_dupes),
        rejections={"UNPARSEABLE_DATE": len(unparseable), "END_BEFORE_START": len(end_before_start), "UNKNOWN_EMPLOYER": len(unknown_emp),
                    "DUPLICATE_KEY_CONFLICT": 2 * len(dup_conflict), "OVERLAP_CONFLICT": 2 * len(overlap), "ORPHAN_HISTORY": len(orphans)},
        no_history_workers=len(no_history), future_starters=len(future), missing_branch_rows=len(missing_branch),
        extract_differences=len(changed),
        headcount_as_of=headcount, headcount_by_employer=dict(sorted(by_emp_hc.items())),
        seniority_evidence_insufficient=sum(1 for k in rejected_workers if k not in overlap and k not in unparseable and any(covers(p, AS_OF) for p in true[k])),
        continuous_service_start=seniority,
        region_change=dict(branch=REGION_CHANGE[0], on=REGION_CHANGE[1].isoformat(), to=REGION_CHANGE[2]),
        closed_branch=dict(branch=CLOSED_BRANCH[0], on=CLOSED_BRANCH[1].isoformat()),
    )
    (out / "answer_key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")
    print(f"wrote {len(hist_df):,} history rows, {len(master_keys):,} workers x 2 extracts; headcount at {AS_OF}: {headcount:,}")


if __name__ == "__main__":
    main()
