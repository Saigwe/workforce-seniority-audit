-- Effective-dated placements: valid rows only. valid_to is inclusive; open placements end on 9999-12-31.
select
    md5(c.record_id) as placement_key,
    c.record_id,
    c.worker_key,
    c.employer_code,
    coalesce(c.branch_code, 'UNASSIGNED') as branch_code,
    c.branch_code is null as is_missing_branch,
    c.start_date as valid_from,
    coalesce(c.end_date, date '9999-12-31') as valid_to,
    c.is_open_ended,
    c.contract_type,
    c.fte,
    s.continuous_service_start
from {{ ref('int_placement_checks') }} c
join {{ ref('int_service_spells') }} s using (record_id)
where c.is_valid
