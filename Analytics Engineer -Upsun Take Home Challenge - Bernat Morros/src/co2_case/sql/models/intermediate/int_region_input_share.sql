with bill_match_keys as (
    select distinct
        b.provider,
        b.sku_description
    from {{ ref('stg_bill_skus') }} as b
    inner join {{ ref('int_project_sku_weights') }} as w
        on b.provider = w.provider
        and b.sku_description = w.sku_description
    where w.total_project_share_for_sku > 0
),
project_totals as (
    select
        region,
        sum(project_share_of_total) as total_input_share
    from {{ ref('stg_project_sku_usage') }}
    group by 1
),
matched_totals as (
    select
        p.region,
        sum(p.project_share_of_total) as matched_input_share
    from {{ ref('stg_project_sku_usage') }} as p
    inner join bill_match_keys as k
        on p.provider = k.provider
        and p.sku_description = k.sku_description
    group by 1
)
select
    t.region,
    t.total_input_share,
    coalesce(m.matched_input_share, 0) as matched_input_share
from project_totals as t
left join matched_totals as m using (region)
