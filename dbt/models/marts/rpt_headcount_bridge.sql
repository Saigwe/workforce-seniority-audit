-- The same question two ways: "how many workers did we have on the as-of date?"
-- Naive: count history rows whose end date is open. Each step applies one rule, ending at the as-of headcount.
with raw as (
    select *, {{ is_open_marker('end_date') }} as is_open, {{ parse_source_date('start_date') }} as start_parsed
    from {{ source('raw', 'placement_history') }}
), h as (select * from {{ ref('int_placement_checks') }}),
s as (
    select
        (select count(*) from raw where is_open) as s0,
        (select count(*) from h where is_open_ended) as s1,
        (select count(*) from h where is_open_ended and coalesce(start_date, date '1900-01-01') <= date '{{ var("as_of") }}') as s2,
        (select count(*) from h where coalesce(start_date, date '1900-01-01') <= date '{{ var("as_of") }}'
            and (is_open_ended or end_date >= date '{{ var("as_of") }}' or end_date is null)) as s3,
        (select count(*) from h where is_valid and start_date <= date '{{ var("as_of") }}' and coalesce(end_date, date '9999-12-31') >= date '{{ var("as_of") }}') as s4,
        (select count(*) from {{ ref('fct_worker_month') }} where month_end = date '{{ var("as_of") }}') as s5
)
select 1 as step_no, 'History rows with an open end date' as step, s0 as change, s0 as running_total from s
union all select 2, 'Exact duplicate rows removed', s1 - s0, s1 from s
union all select 3, 'Starts after the as-of date', s2 - s1, s2 from s
union all select 4, 'Fixed-term placements with a later end date', s3 - s2, s3 from s
union all select 5, 'Rejected rows (conflicts, unparseable dates, orphans)', s4 - s3, s4 from s
union all select 6, 'Workers with two valid rows that day', s5 - s4, s5 from s
union all select 7, 'Headcount at the as-of date', s5, s5 from s
