-- Published report marts are aggregates: none carries a worker key or worker ID.
select table_name, column_name from information_schema.columns
where table_schema = 'gold' and table_name in ('rpt_headcount_asof', 'rpt_headcount_monthly', 'rpt_tenure_bands', 'rpt_quality_summary',
      'rpt_headcount_bridge', 'rpt_reconciliation', 'rpt_rejections_by_source', 'rpt_date_formats', 'rpt_headcount_naive_by_employer')
  and column_name in ('worker_key', 'worker_id', 'record_id')
