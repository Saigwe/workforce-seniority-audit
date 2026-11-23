-- A worker holds one valid placement at a time.
select a.worker_key, a.placement_key, b.placement_key
from {{ ref('fct_placement') }} a
join {{ ref('fct_placement') }} b
  on a.worker_key = b.worker_key and a.placement_key < b.placement_key
 and a.valid_from <= b.valid_to and b.valid_from <= a.valid_to
