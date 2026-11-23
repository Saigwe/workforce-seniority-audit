-- Counts for the audit report: every rule, its severity, rows or workers affected, and the rate.
with h as (select * from {{ ref('int_placement_checks') }}),
raw_rows as (select count(*) as n from {{ source('raw', 'placement_history') }}),
dedup as (select count(*) as n, sum(copies - 1) as dupes from h),
parts as (
    select reason_code, count(*) as affected, 'history rows' as unit from h where not is_valid group by 1
    union all
    select 'NO_HISTORY', count(*), 'workers' from {{ ref('dim_worker') }} where has_no_history
    union all
    select 'MISSING_BRANCH', count(*), 'history rows' from h where is_valid and branch_code is null
    union all
    select 'FUTURE_START', count(*), 'history rows' from h where is_valid and start_date > date '{{ var("as_of") }}'
)
select r.reason_code, r.severity, r.reason, r.rule, coalesce(p.affected, 0) as affected, coalesce(p.unit, 'history rows') as unit,
       case when coalesce(p.unit, 'history rows') = 'workers'
            then coalesce(p.affected, 0) / (select count(*) from {{ ref('dim_worker') }})
            else coalesce(p.affected, 0) / (select n from dedup) end as rate,
       (select n from raw_rows) as raw_rows,
       (select n from dedup) as deduplicated_rows,
       (select dupes from dedup) as exact_duplicate_rows
from {{ ref('rejection_reasons') }} r
left join parts p using (reason_code)
