-- How each payroll system writes dates. Unrecognised values are the ones rejected as unparseable.
select source_system, 'start' as field, start_format as format, count(*) as rows_n from {{ ref('int_placement_checks') }} group by all
union all
select source_system, 'end', end_format, count(*) from {{ ref('int_placement_checks') }} group by all
