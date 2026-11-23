-- Worker master from the latest extract. Natural key: (source_system, worker_id); the two systems reuse numbers, so
-- worker_id alone is not a key. worker_key is the surrogate used everywhere downstream.
with latest as (
    select max(extract_name) as extract_name from {{ source('raw', 'worker_master') }}
)
select
    md5(m.source_system || ':' || m.worker_id) as worker_key,
    m.source_system,
    m.worker_id,
    m.job_family,
    m.home_region,
    {{ parse_source_date('m.record_created') }} as record_created,
    m.extract_name,
    cast(m.extracted_at as timestamp) as extracted_at
from {{ source('raw', 'worker_master') }} m
join latest using (extract_name)
