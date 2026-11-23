-- The rejection table: one row per rejected history row with its reason. Surrogate keys only; no worker detail
-- beyond the key. Published pages show counts from this table, never its rows.
select
    c.record_id,
    c.worker_key,
    c.source_system,
    c.reason_code,
    r.reason,
    r.rule,
    c.start_format,
    c.end_format,
    c.offending_value,
    c.employer_code
from {{ ref('int_placement_checks') }} c
join {{ ref('rejection_reasons') }} r using (reason_code)
where not c.is_valid
