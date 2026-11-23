# Tenure rules

**Completed months of service** between a start date and an as-of date:

```
months = (year(as_of) - year(start)) * 12 + month(as_of) - month(start)
         - 1 if day(as_of) < day(start) and as_of is not the last day of its month
```

The month-end exception means a start late in a month completes each month on the last day of shorter months:

| Start | As of | Months | Why |
|---|---|---|---|
| 15 Jan 2026 | 14 Feb 2026 | 0 | one day short |
| 31 Jan 2026 | 28 Feb 2026 | 1 | February has no 31st; its last day completes the month |
| 31 Jan 2026 | 27 Feb 2026 | 0 | not yet month end |
| 29 Feb 2024 | 28 Feb 2025 | 12 | leap-day start completes the year on 28 February |
| 29 Feb 2024 | 29 Feb 2028 | 48 | next leap day |
| 2 Nov 2026 | 31 Oct 2026 | none | starts after the as-of date |

**Continuous service** is measured with the current employer. Consecutive valid placements with the same employer form
one spell when the gap between the end of one and the start of the next is at most 31 days (`bridge_days`). A longer
gap is a rehire: service restarts. A move to another employer also restarts it.

**Future dates.** A placement starting after the as-of date is valid but not counted; tenure is undefined (null), never
negative. An end date after the as-of date is normal for fixed-term contracts and does not affect tenure.

**Insufficient evidence.** If any history row of a worker is rejected, the start of continuous service cannot be
established, so the worker gets no tenure figure and appears in the band "Insufficient evidence". The rejection table
says which row and why.

All fifteen cases live in `dbt/seeds/tenure_fixtures.csv`; `assert_tenure_fixtures_match` fails the build on a mismatch,
and `tests/test_definitions.py` checks the warehouse against an independent Python implementation.
