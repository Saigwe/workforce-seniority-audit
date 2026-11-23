{#- Completed months of service from start_date to as_of_date, both inclusive of the day.
    Month-end rule: if the as-of date is the last day of its month, a start on a later day-of-month (29, 30, 31)
    has still completed that month. So 31 Jan to 28 Feb is one month, and 29 Feb 2024 to 28 Feb 2025 is twelve.
    Returns null when the start is after the as-of date. -#}
{% macro tenure_months(start_date, as_of_date) -%}
case
    when {{ start_date }} > {{ as_of_date }} then null
    else (year({{ as_of_date }}) - year({{ start_date }})) * 12 + month({{ as_of_date }}) - month({{ start_date }})
         - case when day({{ as_of_date }}) < day({{ start_date }}) and {{ as_of_date }} <> last_day({{ as_of_date }}) then 1 else 0 end
end
{%- endmacro %}

{% macro tenure_band(months) -%}
case
    when {{ months }} is null then null
    when {{ months }} < 6 then '1. Under 6 months'
    when {{ months }} < 12 then '2. 6 to 11 months'
    when {{ months }} < 24 then '3. 1 to 2 years'
    when {{ months }} < 60 then '4. 2 to 5 years'
    else '5. 5 years or more'
end
{%- endmacro %}
