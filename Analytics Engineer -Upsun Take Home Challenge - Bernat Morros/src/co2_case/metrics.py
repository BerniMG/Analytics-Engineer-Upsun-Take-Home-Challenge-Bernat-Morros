from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from .config import ColumnNames
from .modeling import AllocationResult

C = ColumnNames()


def _share(df: pd.DataFrame, numerator: str, denominator_series: pd.Series) -> pd.Series:
    return df[numerator] / denominator_series.sum()


def build_output_tables(allocation: AllocationResult, project: pd.DataFrame) -> dict[str, pd.DataFrame | dict]:
    bill = allocation.bill_with_match_flag.copy()
    project_emissions = allocation.project_emissions_exact.copy()
    overhead = allocation.unallocated_bill_overhead.copy()

    total_bill_kg = bill[C.total_emissions_kg].sum()
    active_project_count = int(project.loc[project[C.project_share] > 0, C.project].nunique())
    total_project_count = int(project[C.project].nunique())

    portfolio_summary = pd.DataFrame([
        {
            'metric': 'total_billed_emissions_kgco2',
            'value': float(total_bill_kg),
        },
        {
            'metric': 'exact_allocated_emissions_kgco2',
            'value': float(project_emissions['exact_allocated_emissions_kgco2'].sum()),
        },
        {
            'metric': 'shared_overhead_emissions_kgco2',
            'value': float(overhead[C.total_emissions_kg].sum()),
        },
        {
            'metric': 'exact_allocation_share',
            'value': float(project_emissions['exact_allocated_emissions_kgco2'].sum() / total_bill_kg),
        },
        {
            'metric': 'shared_overhead_share',
            'value': float(overhead[C.total_emissions_kg].sum() / total_bill_kg),
        },
        {
            'metric': 'projects_total',
            'value': total_project_count,
        },
        {
            'metric': 'projects_with_positive_share',
            'value': active_project_count,
        },
    ])

    usage_mix = (
        bill.groupby(C.usage_category, as_index=False)[C.total_emissions_kg]
        .sum()
        .rename(columns={C.total_emissions_kg: 'billed_emissions_kgco2'})
    )
    usage_mix['share_of_total'] = usage_mix['billed_emissions_kgco2'] / total_bill_kg
    usage_mix = usage_mix.sort_values('billed_emissions_kgco2', ascending=False).reset_index(drop=True)

    product_mix = (
        bill.groupby(C.product_category, as_index=False)[C.total_emissions_kg]
        .sum()
        .rename(columns={C.total_emissions_kg: 'billed_emissions_kgco2'})
    )
    product_mix['share_of_total'] = product_mix['billed_emissions_kgco2'] / total_bill_kg
    product_mix = product_mix.sort_values('billed_emissions_kgco2', ascending=False).reset_index(drop=True)

    usage_coverage = (
        bill.groupby(C.usage_category, as_index=False)
        .agg(
            billed_emissions_kgco2=(C.total_emissions_kg, 'sum'),
            exact_matched_emissions_kgco2=(C.total_emissions_kg, lambda s: s[bill.loc[s.index, 'exact_match_available']].sum()),
        )
    )
    usage_coverage['matched_share'] = (
        usage_coverage['exact_matched_emissions_kgco2'] / usage_coverage['billed_emissions_kgco2']
    )
    usage_coverage = usage_coverage.sort_values('billed_emissions_kgco2', ascending=False).reset_index(drop=True)

    product_coverage = (
        bill.groupby(C.product_category, as_index=False)
        .agg(
            billed_emissions_kgco2=(C.total_emissions_kg, 'sum'),
            exact_matched_emissions_kgco2=(C.total_emissions_kg, lambda s: s[bill.loc[s.index, 'exact_match_available']].sum()),
        )
    )
    product_coverage['matched_share'] = (
        product_coverage['exact_matched_emissions_kgco2'] / product_coverage['billed_emissions_kgco2']
    )
    product_coverage = product_coverage.sort_values('billed_emissions_kgco2', ascending=False).reset_index(drop=True)

    project_hotspots = project_emissions[[C.project, C.region, 'exact_allocated_emissions_kgco2']].copy()
    project_hotspots = project_hotspots.sort_values('exact_allocated_emissions_kgco2', ascending=False).reset_index(drop=True)
    project_hotspots['rank'] = range(1, len(project_hotspots) + 1)
    project_hotspots['cumulative_share'] = (
        project_hotspots['exact_allocated_emissions_kgco2'].cumsum()
        / project_hotspots['exact_allocated_emissions_kgco2'].sum()
    )

    project_match_flag = (
        project.groupby(C.project, as_index=False)
        .agg(total_input_share=(C.project_share, 'sum'))
    )
    matched_project_ids = set(project_hotspots[C.project].tolist())
    project_match_flag['has_exact_allocation'] = project_match_flag[C.project].isin(matched_project_ids)

    project_with_region = project.groupby(C.project, as_index=False)[C.region].first()
    region_total_share = project.groupby(C.region, as_index=False)[C.project_share].sum().rename(columns={C.project_share: 'total_input_share'})
    matched_project_rows = project[project['project_key_provider_sku'].isin(set(bill.loc[bill['exact_match_available'], 'bill_key_provider_sku']))].copy()
    matched_region_share = matched_project_rows.groupby(C.region, as_index=False)[C.project_share].sum().rename(columns={C.project_share: 'matched_input_share'})
    region_allocated = project_hotspots.groupby(C.region, as_index=False)['exact_allocated_emissions_kgco2'].sum()

    region_proxy_intensity = (
        region_total_share
        .merge(matched_region_share, on=C.region, how='left')
        .merge(region_allocated, on=C.region, how='left')
        .fillna({'matched_input_share': 0.0, 'exact_allocated_emissions_kgco2': 0.0})
    )
    region_proxy_intensity['exact_input_coverage'] = (
        region_proxy_intensity['matched_input_share'] / region_proxy_intensity['total_input_share']
    )
    region_proxy_intensity['proxy_intensity_kg_per_input_share'] = (
        region_proxy_intensity['exact_allocated_emissions_kgco2'] / region_proxy_intensity['matched_input_share']
    )
    region_proxy_intensity['is_material_customer_region'] = (
        (region_proxy_intensity['matched_input_share'] >= 0.05)
        & (~region_proxy_intensity[C.region].str.contains('admin|vpn.internal', case=False, na=False))
    )
    material = region_proxy_intensity.loc[region_proxy_intensity['is_material_customer_region']].copy()
    material_avg = material['exact_allocated_emissions_kgco2'].sum() / material['matched_input_share'].sum()
    region_proxy_intensity['proxy_index_vs_material_avg'] = (
        region_proxy_intensity['proxy_intensity_kg_per_input_share'] / material_avg
    )
    region_proxy_intensity = region_proxy_intensity.sort_values('proxy_index_vs_material_avg').reset_index(drop=True)

    current_intensity_per_project = total_bill_kg / total_project_count
    next_year_projects = round(total_project_count * 1.2)
    bau_total = next_year_projects * current_intensity_per_project
    flat_target_total = total_bill_kg
    flat_target_intensity = flat_target_total / next_year_projects
    intensity_reduction_needed = 1 - (flat_target_intensity / current_intensity_per_project)
    current_active_project_intensity = total_bill_kg / active_project_count

    growth_targets = pd.DataFrame([
        {'scenario': 'current_baseline', 'projects': total_project_count, 'total_emissions_kgco2': total_bill_kg, 'intensity_kg_per_project': current_intensity_per_project},
        {'scenario': 'business_as_usual_plus_20pct_projects', 'projects': next_year_projects, 'total_emissions_kgco2': bau_total, 'intensity_kg_per_project': current_intensity_per_project},
        {'scenario': 'flat_absolute_emissions_target', 'projects': next_year_projects, 'total_emissions_kgco2': flat_target_total, 'intensity_kg_per_project': flat_target_intensity},
    ])

    lever_specs = [
        ('reduce_data_transfer_out', bill[C.sku].str.contains('data transfer out', case=False, na=False), 0.10),
        ('right_size_i3_4xlarge_fleet', bill[C.sku].str.contains('i3.4xlarge', case=False, regex=False, na=False), 0.15),
        ('storage_lifecycle_hygiene', bill[C.sku].str.contains('storage|snapshot|gp3|gb-month', case=False, regex=True, na=False), 0.10),
    ]
    lever_rows = []
    for lever_name, mask, illustrative_reduction_rate in lever_specs:
        baseline = float(bill.loc[mask, C.total_emissions_kg].sum())
        lever_rows.append({
            'lever': lever_name,
            'baseline_emissions_kgco2': baseline,
            'illustrative_reduction_rate': illustrative_reduction_rate,
            'illustrative_saving_kgco2': baseline * illustrative_reduction_rate,
        })
    reduction_levers = pd.DataFrame(lever_rows)

    top_1pct_count = max(1, round(total_project_count * 0.01))
    top_5pct_count = max(1, round(total_project_count * 0.05))

    calculation_summary = {
        'projects_with_exact_allocation': int(project_hotspots[C.project].nunique()),
        'weighted_input_share_on_exact_projects': float(
            project_match_flag.loc[project_match_flag['has_exact_allocation'], 'total_input_share'].sum()
        ),
        'top_10_project_concentration': float(
            project_hotspots.head(10)['exact_allocated_emissions_kgco2'].sum() / project_hotspots['exact_allocated_emissions_kgco2'].sum()
        ),
        'top_1pct_project_concentration': float(
            project_hotspots.head(top_1pct_count)['exact_allocated_emissions_kgco2'].sum() / project_hotspots['exact_allocated_emissions_kgco2'].sum()
        ),
        'top_5pct_project_concentration': float(
            project_hotspots.head(top_5pct_count)['exact_allocated_emissions_kgco2'].sum() / project_hotspots['exact_allocated_emissions_kgco2'].sum()
        ),
        'current_intensity_per_project': float(current_intensity_per_project),
        'current_active_project_intensity': float(current_active_project_intensity),
        'flat_target_intensity_per_project': float(flat_target_intensity),
        'required_intensity_reduction_share': float(intensity_reduction_needed),
    }

    return {
        'source_audit': allocation.source_audit,
        'portfolio_summary': portfolio_summary,
        'usage_mix': usage_mix,
        'product_mix': product_mix,
        'usage_coverage': usage_coverage,
        'product_coverage': product_coverage,
        'project_hotspots': project_hotspots,
        'project_match_flag': project_match_flag.merge(project_with_region, on=C.project, how='left'),
        'region_proxy_intensity': region_proxy_intensity,
        'growth_targets': growth_targets,
        'reduction_levers': reduction_levers,
        'project_emissions_exact': project_emissions,
        'unallocated_bill_overhead': overhead,
        'calculation_summary': calculation_summary,
    }


def write_outputs(output_tables: dict[str, pd.DataFrame | dict], output_dir: str | Path) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, obj in output_tables.items():
        if isinstance(obj, pd.DataFrame):
            obj.to_csv(output_dir / f'{name}.csv', index=False)
        elif isinstance(obj, dict):
            (output_dir / f'{name}.json').write_text(pd.Series(obj).to_json(indent=2), encoding='utf-8')
        else:
            raise TypeError(f'Unsupported output type for {name}: {type(obj)}')
