-- As-of snapshot at every month-end: who held a valid placement that day, where, and with how much continuous service.
-- The branch's region is the one in effect on the snapshot date (as-of join to the slowly changing branch dimension).
with months as (
    select cast(last_day(m) as date) as month_end
    from range(date_trunc('month', date '{{ var("snapshot_from") }}'), date '{{ var("as_of") }}' + interval 1 day, interval 1 month) t(m)
), snap as (
    select mo.month_end, p.*
    from months mo
    join {{ ref('fct_placement') }} p on mo.month_end between p.valid_from and p.valid_to
)
select
    s.month_end,
    s.worker_key,
    s.placement_key,
    s.employer_code,
    s.branch_code,
    s.is_missing_branch,
    coalesce(b.region, 'Unassigned') as region,
    s.contract_type,
    s.fte,
    w.has_seniority_evidence,
    case when w.has_seniority_evidence then s.continuous_service_start end as continuous_service_start,
    case when w.has_seniority_evidence then {{ tenure_months('s.continuous_service_start', 's.month_end') }} end as tenure_months,
    case when w.has_seniority_evidence then {{ tenure_band(tenure_months('s.continuous_service_start', 's.month_end')) }}
         else '6. Insufficient evidence' end as tenure_band
from snap s
join {{ ref('dim_worker') }} w using (worker_key)
left join {{ ref('dim_branch') }} b
  on b.branch_code = s.branch_code and s.month_end between b.valid_from and coalesce(b.valid_to, date '9999-12-31')
