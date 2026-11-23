select
    month_end,
    employer_code,
    count(*) as workers,
    count(*) filter (where has_seniority_evidence) as workers_with_seniority,
    count(*) filter (where is_missing_branch) as missing_branch,
    avg(tenure_months) as avg_tenure_months
from {{ ref('fct_worker_month') }}
group by 1, 2
