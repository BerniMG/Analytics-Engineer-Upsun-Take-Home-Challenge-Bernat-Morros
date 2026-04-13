from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import ColumnNames, DEFAULT_TOLERANCE, MICRO_ROW_THRESHOLD_KG

C = ColumnNames()


@dataclass
class AllocationResult:
    source_audit: dict
    bill_with_match_flag: pd.DataFrame
    project_emissions_exact: pd.DataFrame
    row_level_allocations: pd.DataFrame
    unallocated_bill_overhead: pd.DataFrame


def audit_source_grain(bill: pd.DataFrame, project: pd.DataFrame) -> dict:
    bill_provider_sku = bill[[C.provider, C.sku]].drop_duplicates()
    project_provider_sku = project[[C.provider, C.sku]].drop_duplicates()

    bill_key_set = set(map(tuple, bill_provider_sku.to_numpy()))
    project_key_set = set(map(tuple, project_provider_sku.to_numpy()))

    project_region_max = int(project.groupby(C.project)[C.region].nunique().max())

    audit = {
        'bill_rows': int(len(bill)),
        'bill_unique_sku_descriptions': int(bill[C.sku].nunique()),
        'bill_unique_provider_sku': int(len(bill_provider_sku)),
        'bill_unique_provider_sku_product': int(
            bill[[C.provider, C.sku, C.product_category]].drop_duplicates().shape[0]
        ),
        'bill_unique_full_grain': int(
            bill[[C.provider, C.sku, C.product_category, C.usage_category]].drop_duplicates().shape[0]
        ),
        'duplicate_provider_sku_groups': int(
            (bill.groupby([C.provider, C.sku]).size() > 1).sum()
        ),
        'provider_sku_multi_product_category_groups': int(
            (bill.groupby([C.provider, C.sku])[C.product_category].nunique() > 1).sum()
        ),
        'provider_sku_multi_usage_category_groups': int(
            (bill.groupby([C.provider, C.sku])[C.usage_category].nunique() > 1).sum()
        ),
        'bill_zero_emission_rows': int((bill[C.total_emissions_kg] == 0).sum()),
        'bill_micro_rows_leq_1e_6': int((bill[C.total_emissions_kg] <= MICRO_ROW_THRESHOLD_KG).sum()),
        'bill_total_kg': float(bill[C.total_emissions_kg].sum()),
        'project_rows': int(len(project)),
        'project_unique_projects': int(project[C.project].nunique()),
        'project_active_projects_positive_share': int(project.loc[project[C.project_share] > 0, C.project].nunique()),
        'project_unique_regions': int(project[C.region].nunique()),
        'project_positive_rows': int((project[C.project_share] > 0).sum()),
        'project_share_total': float(project[C.project_share].sum()),
        'max_regions_per_project': project_region_max,
        'exact_overlap_provider_sku': int(len(bill_key_set & project_key_set)),
        'bill_only_provider_sku': int(len(bill_key_set - project_key_set)),
        'project_only_provider_sku': int(len(project_key_set - bill_key_set)),
    }

    project_share_by_key = (
        project.groupby([C.provider, C.sku], as_index=False)[C.project_share]
        .sum()
        .rename(columns={C.project_share: 'project_share_by_key'})
    )
    project_share_by_key['in_bill'] = [
        t in bill_key_set for t in map(tuple, project_share_by_key[[C.provider, C.sku]].to_numpy())
    ]
    audit['project_only_share_total'] = float(
        project_share_by_key.loc[~project_share_by_key['in_bill'], 'project_share_by_key'].sum()
    )

    whitespace_normalized = bill[[C.provider, C.sku, C.product_category, C.usage_category]].copy()
    for column in [C.provider, C.sku, C.product_category, C.usage_category]:
        whitespace_normalized[column] = whitespace_normalized[column].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
    audit['whitespace_only_near_duplicate_full_grain_groups'] = int(
        len(bill) - whitespace_normalized.drop_duplicates().shape[0]
    )

    return audit


def build_exact_match_allocation(bill: pd.DataFrame, project: pd.DataFrame) -> AllocationResult:
    audit = audit_source_grain(bill, project)

    weights = (
        project.groupby([C.provider, C.sku], as_index=False)[C.project_share]
        .sum()
        .rename(columns={C.project_share: 'total_project_share_for_sku'})
    )

    bill_with_match_flag = bill.merge(weights, on=[C.provider, C.sku], how='left')
    bill_with_match_flag['exact_match_available'] = bill_with_match_flag['total_project_share_for_sku'].fillna(0) > 0

    row_level = (
        bill_with_match_flag.merge(
            project[[C.provider, C.sku, C.project, C.region, C.project_share]],
            on=[C.provider, C.sku],
            how='left',
        )
        .copy()
    )
    row_level['matched_project_row'] = (
        row_level['exact_match_available']
        & row_level[C.project_share].fillna(0).gt(0)
    )
    row_level['allocated_emissions_kgco2'] = np.where(
        row_level['matched_project_row'],
        row_level[C.total_emissions_kg] * row_level[C.project_share] / row_level['total_project_share_for_sku'],
        0.0,
    )
    row_level['allocation_method'] = np.where(
        row_level['matched_project_row'],
        'exact_provider_plus_sku',
        'shared_overhead',
    )

    project_emissions_exact = (
        row_level.loc[row_level['matched_project_row']]
        .groupby([C.project, C.region], as_index=False)
        .agg(
            exact_allocated_emissions_kgco2=('allocated_emissions_kgco2', 'sum'),
            matched_input_share=(C.project_share, 'sum'),
        )
        .sort_values('exact_allocated_emissions_kgco2', ascending=False)
        .reset_index(drop=True)
    )

    unallocated_bill_overhead = (
        bill_with_match_flag.loc[~bill_with_match_flag['exact_match_available']]
        .copy()
        .assign(allocation_method='shared_overhead')
    )

    billed_total = float(bill[C.total_emissions_kg].sum())
    allocated_total = float(project_emissions_exact['exact_allocated_emissions_kgco2'].sum())
    unallocated_total = float(unallocated_bill_overhead[C.total_emissions_kg].sum())
    if abs((allocated_total + unallocated_total) - billed_total) > DEFAULT_TOLERANCE:
        raise ValueError('Reconciliation failed: allocated + unallocated does not match billed total.')

    return AllocationResult(
        source_audit=audit,
        bill_with_match_flag=bill_with_match_flag,
        project_emissions_exact=project_emissions_exact,
        row_level_allocations=row_level,
        unallocated_bill_overhead=unallocated_bill_overhead,
    )
