select * from {{ ref('rpt_tenure_fixtures') }} where computed_months is distinct from expected_months
