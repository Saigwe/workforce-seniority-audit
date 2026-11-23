-- Placement history, typed. Exact duplicate rows (every field equal) are collapsed; the count is kept for the audit.
-- Raw date text and its detected format are kept next to the parsed date so every rejection can be explained.
with typed as (
    select
        record_id,
        source_system,
        worker_id,
        md5(source_system || ':' || worker_id) as worker_key,
        trim(employer_code) as employer_code,
        nullif(trim(branch_code), '') as branch_code,
        start_date as start_raw,
        end_date as end_raw,
        {{ source_date_format('start_date') }} as start_format,
        {{ source_date_format('end_date') }} as end_format,
        {{ parse_source_date('start_date') }} as start_date,
        {{ parse_source_date('end_date') }} as end_date,
        {{ is_open_marker('end_date') }} as is_open_ended,
        contract_type,
        cast(fte as double) as fte,
        cast(extracted_at as timestamp) as extracted_at
    from {{ source('raw', 'placement_history') }}
), numbered as (
    select *,
           row_number() over (partition by source_system, worker_id, employer_code, coalesce(branch_code, ''), start_raw, end_raw, contract_type, fte
                              order by record_id) as copy_no,
           count(*) over (partition by source_system, worker_id, employer_code, coalesce(branch_code, ''), start_raw, end_raw, contract_type, fte) as copies
    from typed
)
select * exclude (copy_no) from numbered where copy_no = 1
