select * from {{ ref('rpt_reconciliation') }}
where workers <> (select workers from {{ ref('rpt_reconciliation') }} where cut = 'total')
