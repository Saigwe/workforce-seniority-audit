select * from (select sum(change) filter (where step_no < 7) as bridged, max(running_total) filter (where step_no = 7) as headcount
               from {{ ref('rpt_headcount_bridge') }})
where bridged <> headcount
