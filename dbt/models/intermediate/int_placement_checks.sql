-- Every deduplicated history row gets at most one rejection reason, in a fixed order, so each row is either valid or
-- rejected for exactly one documented reason. Overlap is only checked between rows that passed every earlier rule.
with h as (
    select h.*,
           m.worker_key is not null as in_master,
           e.employer_code is not null as known_employer,
           count(*) over (partition by h.source_system, h.worker_id, h.employer_code, coalesce(cast(h.start_date as varchar), h.start_raw)) as rows_per_natural_key
    from {{ ref('stg_placement_history') }} h
    left join {{ ref('stg_worker_master') }} m using (worker_key)
    left join {{ ref('stg_employers') }} e on e.employer_code = h.employer_code
), first_pass as (
    select *,
        case
            when not in_master then 'ORPHAN_HISTORY'
            when start_date is null or (not is_open_ended and end_date is null) then 'UNPARSEABLE_DATE'
            when end_date < start_date then 'END_BEFORE_START'
            when not known_employer then 'UNKNOWN_EMPLOYER'
            when rows_per_natural_key > 1 then 'DUPLICATE_KEY_CONFLICT'
        end as reason_code
    from h
), overlap_rows as (
    select distinct a.record_id
    from first_pass a
    join first_pass b
      on a.worker_key = b.worker_key and a.record_id <> b.record_id
     and a.employer_code <> b.employer_code
     and a.start_date <= coalesce(b.end_date, date '9999-12-31')
     and b.start_date <= coalesce(a.end_date, date '9999-12-31')
    where a.reason_code is null and b.reason_code is null
)
select f.* exclude (reason_code, in_master, known_employer, rows_per_natural_key),
       coalesce(f.reason_code, case when o.record_id is not null then 'OVERLAP_CONFLICT' end) as reason_code,
       coalesce(f.reason_code, case when o.record_id is not null then 'OVERLAP_CONFLICT' end) is null as is_valid,
       case
           when f.reason_code = 'UNPARSEABLE_DATE' and f.start_date is null then f.start_raw
           when f.reason_code = 'UNPARSEABLE_DATE' then f.end_raw
           when f.reason_code = 'END_BEFORE_START' then f.start_raw || ' > ' || f.end_raw
           when f.reason_code = 'UNKNOWN_EMPLOYER' then f.employer_code
       end as offending_value
from first_pass f
left join overlap_rows o using (record_id)
