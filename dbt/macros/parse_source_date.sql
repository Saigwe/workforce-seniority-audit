{#- Parse a source date written in any of the formats the payroll systems use. Returns null for an open-ended marker
    and for anything unparseable; pair it with is_open_marker() and source_date_format() to tell the two apart. -#}
{% macro parse_source_date(col) -%}
case
    when {{ is_open_marker(col) }} then null
    when regexp_full_match(trim({{ col }}), '\d{4}-\d{2}-\d{2}') then cast(try_strptime(trim({{ col }}), '%Y-%m-%d') as date)
    when regexp_full_match(trim({{ col }}), '\d{2}/\d{2}/\d{4}') then cast(try_strptime(trim({{ col }}), '%d/%m/%Y') as date)
    when regexp_full_match(trim({{ col }}), '\d{8}') then cast(try_strptime(trim({{ col }}), '%Y%m%d') as date)
    when regexp_full_match(trim({{ col }}), '\d{4,5}') then cast(date '1899-12-30' + cast(trim({{ col }}) as integer) as date)
end
{%- endmacro %}

{% macro is_open_marker(col) -%}
(coalesce(trim({{ col }}), '') in ('', '9999-12-31', '31/12/9999'))
{%- endmacro %}

{% macro source_date_format(col) -%}
case
    when {{ is_open_marker(col) }} then 'open'
    when regexp_full_match(trim({{ col }}), '\d{4}-\d{2}-\d{2}') then 'YYYY-MM-DD'
    when regexp_full_match(trim({{ col }}), '\d{2}/\d{2}/\d{4}') then 'DD/MM/YYYY'
    when regexp_full_match(trim({{ col }}), '\d{8}') then 'YYYYMMDD'
    when regexp_full_match(trim({{ col }}), '\d{4,5}') then 'spreadsheet serial'
    else 'unrecognised'
end
{%- endmacro %}
