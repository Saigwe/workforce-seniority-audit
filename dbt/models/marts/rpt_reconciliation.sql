-- Eligible headcount at the as-of date must be the same total under every filter: by employer, by branch (including
-- unassigned) and by region.
with f as (select * from {{ ref('fct_worker_month') }} where month_end = date '{{ var("as_of") }}')
select 'total' as cut, count(*) as workers from f
union all select 'sum over employers', sum(n) from (select employer_code, count(*) n from f group by 1)
union all select 'sum over branches incl. unassigned', sum(n) from (select branch_code, count(*) n from f group by 1)
union all select 'sum over regions', sum(n) from (select region, count(*) n from f group by 1)
union all select 'sum over tenure bands', sum(n) from (select tenure_band, count(*) n from f group by 1)
