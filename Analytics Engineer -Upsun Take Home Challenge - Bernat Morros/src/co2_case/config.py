from __future__ import annotations

from dataclasses import dataclass


BILL_REQUIRED_COLUMNS = [
    "provider",
    "SKU Description",
    "Product category",
    "Usage category",
    "Total emissions kgCO2",
]

PROJECT_REQUIRED_COLUMNS = [
    "provider",
    "SKU Description",
    "Project",
    "Region",
    "Emissions kgCO2 % of total emissions",
]

DEFAULT_TOLERANCE = 1e-9
MICRO_ROW_THRESHOLD_KG = 1e-6


@dataclass(frozen=True)
class ColumnNames:
    provider: str = "provider"
    sku: str = "SKU Description"
    product_category: str = "Product category"
    usage_category: str = "Usage category"
    total_emissions_kg: str = "Total emissions kgCO2"
    project: str = "Project"
    region: str = "Region"
    project_share: str = "Emissions kgCO2 % of total emissions"
