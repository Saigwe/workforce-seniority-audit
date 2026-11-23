-- Raw rows = deduplicated rows + exact duplicates; deduplicated rows = valid + rejected.
with q as (select * from {{ ref('rpt_quality_summary') }} limit 1)
select * from q
where raw_rows <> deduplicated_rows + exact_duplicate_rows
   or deduplicated_rows <> (select count(*) from {{ ref('fct_placement') }}) + (select count(*) from {{ ref('rpt_rejections') }})
