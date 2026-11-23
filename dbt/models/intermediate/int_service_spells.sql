-- Continuous service with one employer: consecutive valid placements with the same employer are one spell when the
-- gap between them is at most bridge_days. A longer gap, or a move to another employer, starts a new spell.
with p as (
    select worker_key, employer_code, record_id, start_date, coalesce(end_date, date '9999-12-31') as end_date
    from {{ ref('int_placement_checks') }}
    where is_valid
), flagged as (
    select *,
           case when lag(end_date) over w is null
                  or start_date - lag(end_date) over w > {{ var('bridge_days') }} + 1 then 1 else 0 end as new_spell
    from p
    window w as (partition by worker_key, employer_code order by start_date)
), numbered as (
    select *, sum(new_spell) over (partition by worker_key, employer_code order by start_date rows unbounded preceding) as spell_no
    from flagged
)
select *, min(start_date) over (partition by worker_key, employer_code, spell_no) as continuous_service_start
from numbered
