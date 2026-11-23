select source_system, reason_code, count(*) as rows_rejected,
       count(*) / any_value(t.n) as rate
from {{ ref('rpt_rejections') }}
join (select source_system, count(*) as n from {{ ref('int_placement_checks') }} group by 1) t using (source_system)
group by 1, 2
