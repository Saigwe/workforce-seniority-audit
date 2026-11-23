-- Naive against as-of headcount by employer, so the difference can be traced to an employer.
with naive as (
    select employer_code, count(*) as naive_open_rows
    from {{ source('raw', 'placement_history') }}
    where {{ is_open_marker('end_date') }}
    group by 1
), as_of_count as (
    select employer_code, count(*) as headcount
    from {{ ref('fct_worker_month') }} where month_end = date '{{ var("as_of") }}' group by 1
)
select coalesce(n.employer_code, a.employer_code) as employer_code, coalesce(n.naive_open_rows, 0) as naive_open_rows,
       coalesce(a.headcount, 0) as headcount
from naive n full join as_of_count a using (employer_code)
