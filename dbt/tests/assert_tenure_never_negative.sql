select * from {{ ref('fct_worker_month') }} where tenure_months < 0 or (has_seniority_evidence and tenure_months is null)
