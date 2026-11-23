-- Headcount at the as-of date by employer, branch and region, with the tenure band. Cells below min_cell are flagged
-- for suppression on published pages; totals are computed before suppression so they always reconcile.
select
    f.employer_code,
    e.employer_name,
    f.branch_code,
    f.region,
    f.tenure_band,
    count(*) as workers,
    count(*) < {{ var('min_cell') }} as is_small_cell
from {{ ref('fct_worker_month') }} f
join {{ ref('dim_employer') }} e using (employer_code)
where f.month_end = date '{{ var("as_of") }}'
group by all
