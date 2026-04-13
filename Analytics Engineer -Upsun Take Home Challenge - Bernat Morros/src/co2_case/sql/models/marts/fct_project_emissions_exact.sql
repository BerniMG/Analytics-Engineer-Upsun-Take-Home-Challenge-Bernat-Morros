with bill as (
    select * from {{ ref('int_bill_match_coverage') }}
    where exact_match_available
),
project_usage as (
    select * from {{ ref('stg_project_sku_usage') }}
),
row_level as (
    select
        bill.provider,
        bill.sku_description,
        bill.product_category,
        bill.usage_category,
        project_usage.project_id,
        project_usage.region,
        project_usage.project_share_of_total,
        bill.total_project_share_for_sku,
        bill.total_emissions_kgco2 * safe_divide(project_usage.project_share_of_total, bill.total_project_share_for_sku)
            as allocated_emissions_kgco2,
        'exact_provider_plus_sku' as allocation_method
    from bill
    join project_usage
      on bill.provider = project_usage.provider
     and bill.sku_description = project_usage.sku_description
    where project_usage.project_share_of_total > 0
)
select * from row_level
