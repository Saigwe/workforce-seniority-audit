select tenure_band, count(*) as workers, count(*) / sum(count(*)) over () as share
from {{ ref('fct_worker_month') }}
where month_end = date '{{ var("as_of") }}'
group by 1
