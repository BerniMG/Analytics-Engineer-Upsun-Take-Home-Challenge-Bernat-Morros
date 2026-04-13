select
    bill.provider,
    bill.sku_description,
    bill.product_category,
    bill.usage_category,
    bill.total_emissions_kgco2,
    bill.bill_key_provider_sku,
    bill.bill_key_full_grain,
    'shared_overhead' as allocation_method
from {{ ref('int_bill_match_coverage') }} as bill
where not bill.exact_match_available
