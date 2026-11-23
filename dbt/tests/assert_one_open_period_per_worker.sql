select worker_key, count(*) from {{ ref('fct_placement') }} where is_open_ended group by 1 having count(*) > 1
