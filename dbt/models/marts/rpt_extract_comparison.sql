-- Are the two worker-master extracts the same? Same header and row count is not proof; compare every field by key.
with a as (select * from {{ source('raw', 'worker_master') }} where extract_name = 'worker_master_a'),
b as (select * from {{ source('raw', 'worker_master') }} where extract_name = 'worker_master_b')
select
    (select count(*) from a) as rows_a,
    (select count(*) from b) as rows_b,
    count(*) filter (where a.worker_id is null) as only_in_b,
    count(*) filter (where b.worker_id is null) as only_in_a,
    count(*) filter (where a.job_family is distinct from b.job_family and a.worker_id is not null and b.worker_id is not null) as job_family_differs,
    count(*) filter (where a.home_region is distinct from b.home_region and a.worker_id is not null and b.worker_id is not null) as home_region_differs,
    count(*) filter (where a.record_created is distinct from b.record_created and a.worker_id is not null and b.worker_id is not null) as record_created_differs
from a full join b using (source_system, worker_id)
