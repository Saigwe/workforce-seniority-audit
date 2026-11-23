select employer_code, employer_name, sector from {{ source('raw', 'employers') }}
