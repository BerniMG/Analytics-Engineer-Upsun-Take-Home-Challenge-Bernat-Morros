with exact_alloc as (
    select sum(allocated_emissions_kgco2) as exact_allocated_emissions_kgco2
    from {{ ref('fct_project_emissions_exact') }}
),
shared_overhead as (
    select sum(total_emissions_kgco2) as shared_overhead_emissions_kgco2
    from {{ ref('fct_unallocated_bill_overhead') }}
),
total_bill as (
    select sum(total_emissions_kgco2) as total_billed_emissions_kgco2
    from {{ ref('stg_bill_skus') }}
)
select
    total_bill.total_billed_emissions_kgco2,
    exact_alloc.exact_allocated_emissions_kgco2,
    shared_overhead.shared_overhead_emissions_kgco2,
    safe_divide(exact_alloc.exact_allocated_emissions_kgco2, total_bill.total_billed_emissions_kgco2) as exact_allocation_share,
    safe_divide(shared_overhead.shared_overhead_emissions_kgco2, total_bill.total_billed_emissions_kgco2) as shared_overhead_share
from total_bill, exact_alloc, shared_overhead
