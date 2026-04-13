with region_input as (
    select * from {{ ref('int_region_input_share') }}
),
allocated as (
    select
        region,
        sum(allocated_emissions_kgco2) as exact_allocated_emissions_kgco2
    from {{ ref('fct_project_emissions_exact') }}
    group by 1
)
select
    region_input.region,
    region_input.total_input_share,
    region_input.matched_input_share,
    allocated.exact_allocated_emissions_kgco2,
    safe_divide(region_input.matched_input_share, region_input.total_input_share) as exact_input_coverage,
    safe_divide(allocated.exact_allocated_emissions_kgco2, region_input.matched_input_share) as proxy_intensity_kg_per_input_share
from region_input
left join allocated using (region)
