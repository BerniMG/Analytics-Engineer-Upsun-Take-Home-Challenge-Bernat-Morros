with bill as (
    select * from {{ ref('stg_bill_skus') }}
),
weights as (
    select * from {{ ref('int_project_sku_weights') }}
)
select
    bill.*,
    weights.total_project_share_for_sku,
    coalesce(weights.total_project_share_for_sku, 0) > 0 as exact_match_available
from bill
left join weights
  on bill.provider = weights.provider
 and bill.sku_description = weights.sku_description
