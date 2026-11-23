# Metric dictionary

| Metric | Definition | Grain |
|---|---|---|
| **Headcount (eligible)** | Workers with a valid placement covering the date (start on or before, end on or after) | date x employer, branch, region, band |
| **Naive open-row count** | History rows whose end date is blank or 9999; shown only to explain the difference | date |
| **Tenure months** | Completed months of continuous service with the current employer, month-end rule | worker x date |
| **Tenure band** | Under 6 months, 6 to 11 months, 1 to 2 years, 2 to 5 years, 5 years or more, Insufficient evidence | worker x date |
| **Rejection rate** | Rejected rows over deduplicated rows, by reason or source system | extract |
| **Missing branch assignments** | Workers on the date whose placement has no branch; reported as Unassigned | date x employer |
| **No-history workers** | Workers in the master extract with no placement rows | extract |
| **Extract differences** | Fields that differ between the two worker-master extracts, matched on the natural key | extract pair |

Every breakdown on a published page is suppressed below five workers. Totals are computed before suppression and
reconcile under every filter.
