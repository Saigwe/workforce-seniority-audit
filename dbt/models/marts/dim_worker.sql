-- One row per worker (surrogate key). Attributes only: there are no names, birth dates or identifiers in this project.
with hist as (
    select worker_key,
           count(*) as history_rows,
           count(*) filter (where is_valid) as valid_rows,
           count(*) filter (where not is_valid) as rejected_rows,
           min(start_date) filter (where is_valid) as first_valid_start
    from {{ ref('int_placement_checks') }}
    group by 1
)
select m.worker_key, m.source_system, m.worker_id, m.job_family, m.home_region,
       coalesce(h.history_rows, 0) as history_rows,
       coalesce(h.valid_rows, 0) as valid_rows,
       coalesce(h.rejected_rows, 0) as rejected_rows,
       h.worker_key is null as has_no_history,
       coalesce(h.rejected_rows, 0) = 0 and h.worker_key is not null as has_seniority_evidence,
       h.first_valid_start
from {{ ref('stg_worker_master') }} m
left join hist h using (worker_key)
