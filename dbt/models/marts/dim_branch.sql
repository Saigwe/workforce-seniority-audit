-- Slowly changing: one row per branch per effective period. Join on the date the fact refers to.
select * from {{ ref('stg_branches') }}
union all
select md5('UNASSIGNED'), 'UNASSIGNED', null, 'No branch recorded', 'Unassigned', date '1900-01-01', null
