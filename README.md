# Workforce seniority and data-quality audit

[![ci](https://github.com/Saigwe/workforce-seniority-audit/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Saigwe/workforce-seniority-audit/actions/workflows/ci.yml)
[![dashboards](https://github.com/Saigwe/workforce-seniority-audit/actions/workflows/pages.yml/badge.svg?branch=main)](https://saigwe.github.io/workforce-seniority-audit/)

**Live dashboards: [saigwe.github.io/workforce-seniority-audit](https://saigwe.github.io/workforce-seniority-audit/)**

Turns inconsistent worker records into an auditable, as-of view for workforce reporting, and says plainly which
workers lack the evidence to calculate seniority. Two payroll systems deliver worker extracts and placement history
with mixed date formats, impossible dates, three spellings of "open-ended", duplicate rows, conflicting employer
assignments, rehires, gaps and missing branches. Staging types them, every row is either valid or rejected for one
documented reason, and an effective-dated placement model answers "how many workers did we have on this date, and how
long have they served?" the same way under every filter.

Built end to end: a seeded synthetic generator, source contracts, a dbt warehouse on DuckDB, tenure-rule fixtures, five
web dashboards, an audit report, a metric dictionary and DAX measures. The scenario is modelled on worker master-data
and seniority reporting for a payroll services provider.

**Everything here is invented.** Meridian Workforce Services, its client employers, branches and workers come from
`generator/simulate.py`. There are no names, birth dates or identifiers anywhere: workers are generated numbers. The
results are demo results, not any company's figures. Published pages show counts only, and cells under five workers
are suppressed.

## The question, answered twice

"How many workers did we have on 31 October 2026?" From the current build ([analysis/audit_report.md](analysis/audit_report.md)):

| Rule applied | Count |
|---|---|
| History rows with an open end date (the naive answer) | 1,706 |
| Remove exact duplicate rows | 1,683 |
| Remove placements that start after the as-of date | 1,663 |
| Add fixed-term placements whose end date is after the as-of date | 2,029 |
| Remove rejected rows (conflicting employers, unparseable dates, orphans) | **1,959** |

The naive answer is 13% low, mostly because fixed-term placements carry a real end date and are missed by a filter on
blank end dates. Of the 1,959, **1,941** have a seniority figure; **18** hold a valid placement but have a rejected row
elsewhere in their history, so they are reported as insufficient evidence rather than given a guessed start date.

## What the audit finds

| Finding | Where |
|---|---|
| 6,892 history rows delivered; 40 exact duplicates; 104 rows rejected (1.5%) for one of six reasons, each with a code | Data quality |
| 40 rows place a worker with two employers at once; both rows are rejected and the worker is listed for review | Data quality |
| 25 start dates cannot be parsed or do not exist (31/02/2024, 2023-13-01, N/A) | Data quality |
| The two payroll systems reuse 15 worker numbers for different people; the natural key is system plus ID | Data quality |
| The two worker-master extracts have the same header and row count but differ for 4 workers | Data quality |
| 70 workers on 31 October have no branch recorded; they are reported as Unassigned so branch totals still reconcile | Headcount |
| 35 workers in the master have no history; 21 placements start after the as-of date | Data quality |

## Rules

- **Natural and surrogate keys.** A worker is (source system, worker ID); `worker_key` is an md5 surrogate. A placement's
  natural key is (worker, employer, start date).
- **Effective dating.** A placement counts on a date if it started on or before it and ends on or after it (inclusive). Open
  ends are blank, `9999-12-31` or `31/12/9999`. Branch region is joined as of the same date (the branch dimension is slowly changing).
- **One reason per rejected row**, checked in order: orphan history, unparseable date, end before start, unknown
  employer, duplicate key with different details, overlap with another employer. Flags (missing branch, no history,
  future start) never reject a row.
- **Continuous service** is with the current employer; gaps of up to 31 days are bridged; a longer gap or a change of
  employer restarts it.
- **Completed months** follow a month-end rule: 31 January to 28 February is one month; 29 February 2024 to 28 February 2025
  is twelve. Fifteen fixtures in `dbt/seeds/tenure_fixtures.csv` run on every build. See [docs/tenure_rules.md](docs/tenure_rules.md).
- **Future dates** are valid but do not count until they start; tenure is undefined before the start.

## How it fits together

```
generator/simulate.py  ->  data/raw/*.parquet (4 tables, every column text) + answer key
contracts/sources.yml  ->  columns, text type and grain each extract must meet (tests/test_contracts.py)
dbt/ (DuckDB)          ->  silver: typed staging, placement checks, service spells
                       ->  gold:   dim_worker, dim_employer, dim_branch (SCD), fct_placement (effective-dated),
                                   fct_worker_month (as-of snapshot), rejection table, 11 report marts
dashboards/            ->  export.py (aggregates only) -> data.json -> build.py -> 5 static pages, GitHub Pages
analysis/              ->  audit_report.py -> audit_report.md, fingerprint.py
bi/                    ->  DAX measures
docs/                  ->  metric dictionary, tenure rules, design decisions, demo script
```

## What is tested

- Every delivered row is valid, an exact duplicate, or rejected once; no worker holds two valid placements at once.
- Headcount, headcount by employer and every worker's continuous-service start equal the generator's ground truth.
- Tenure matches the fixtures and an independent Python implementation on a sample of the warehouse.
- Headcount reconciles by employer, branch (including unassigned), region and tenure band.
- Branch region is the one in effect on the snapshot date; a closed branch has no workers after closing.
- Duplicate natural keys, open-ended periods, overlap, no-history workers, month-end anniversaries and leap years each have a test.
- Published marts and the dashboard export contain no worker keys, IDs or rows.
- CI regenerates from the same seed, rebuilds, and compares a fingerprint of every gold mart.

## Run it

```bash
pip install -r requirements.txt
make all        # generate, dbt build, dashboards and the audit report
make rebuild    # regenerate and rebuild: every gold mart must be identical
make test       # pytest against the built warehouse
make serve      # dashboards on http://localhost:8000
```

On Windows without `make`, run the commands in the `Makefile` in order. The as-of date, bridge days and minimum cell
size are dbt vars in `dbt/dbt_project.yml`.

## Licence

MIT. Synthetic data only.
