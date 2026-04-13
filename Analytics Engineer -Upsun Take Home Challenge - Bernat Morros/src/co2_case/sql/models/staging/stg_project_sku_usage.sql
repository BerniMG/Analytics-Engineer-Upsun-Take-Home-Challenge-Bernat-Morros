with source as (
    select * from {{ source('raw', 'project_sku_usage') }}
)
select
    trim(provider) as provider,
    trim(`SKU Description`) as sku_description,
    trim(project) as project_id,
    trim(region) as region,
    cast(`Emissions kgCO2 % of total emissions` as numeric) as project_share_of_total,
    concat(trim(provider), ' || ', trim(`SKU Description`)) as project_key_provider_sku
from source
