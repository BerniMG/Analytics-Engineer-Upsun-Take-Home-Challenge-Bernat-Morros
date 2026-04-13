with project_count as (
    select count(distinct project_id) as projects from {{ ref('stg_project_sku_usage') }}
),
portfolio as (
    select total_billed_emissions_kgco2 from {{ ref('mart_portfolio_summary') }}
)
select
    projects as current_projects,
    cast(round(projects * 1.2, 0) as int64) as next_year_projects,
    total_billed_emissions_kgco2 as current_total_emissions_kgco2,
    safe_divide(total_billed_emissions_kgco2, projects) as current_intensity_kg_per_project,
    safe_divide(total_billed_emissions_kgco2, cast(round(projects * 1.2, 0) as int64)) as flat_target_intensity_kg_per_project
from project_count, portfolio
