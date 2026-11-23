-- Branch reference, effective-dated. valid_to is inclusive; null means current.
select
    md5(branch_code || ':' || valid_from) as branch_sk,
    branch_code,
    employer_code,
    branch_name,
    region,
    cast(valid_from as date) as valid_from,
    cast(nullif(valid_to, '') as date) as valid_to
from {{ source('raw', 'branches') }}
