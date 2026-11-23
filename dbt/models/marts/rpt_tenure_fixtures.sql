-- The tenure rule run on documented edge cases (dbt/seeds/tenure_fixtures.csv); a test fails on any mismatch.
select case_id, start_date, as_of_date, expected_months, note,
       {{ tenure_months('start_date', 'as_of_date') }} as computed_months
from {{ ref('tenure_fixtures') }}
