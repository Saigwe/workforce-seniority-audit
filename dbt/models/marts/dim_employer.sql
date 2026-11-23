select employer_code, employer_name, sector from {{ ref('stg_employers') }}
union all
select 'UNKNOWN', 'Unknown employer', 'Unknown'
