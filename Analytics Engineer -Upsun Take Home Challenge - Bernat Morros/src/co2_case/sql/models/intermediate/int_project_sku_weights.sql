select
    provider,
    sku_description,
    sum(project_share_of_total) as total_project_share_for_sku
from {{ ref('stg_project_sku_usage') }}
group by 1, 2
