with source as (
    select * from {{ source('raw', 'bill_skus') }}
)
select
    trim(provider) as provider,
    trim(`SKU Description`) as sku_description,
    trim(`Product category`) as product_category,
    trim(`Usage category`) as usage_category,
    cast(`Total emissions kgCO2` as numeric) as total_emissions_kgco2,
    concat(trim(provider), ' || ', trim(`SKU Description`)) as bill_key_provider_sku,
    concat(
        trim(provider), ' || ', trim(`SKU Description`), ' || ', trim(`Product category`), ' || ', trim(`Usage category`)
    ) as bill_key_full_grain
from source
