from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from co2_case.charts import CHART_FILENAMES, write_charts_from_output_tables
from co2_case.io import load_source_data
from co2_case.metrics import build_output_tables
from co2_case.modeling import build_exact_match_allocation

WORKBOOK = PROJECT_ROOT / "sources" / "xlsx" / "AE_Take_home_challenge.xlsx"


@pytest.mark.skipif(not WORKBOOK.is_file(), reason=f"workbook missing: {WORKBOOK}")
def test_reconciliation() -> None:
    source = load_source_data(WORKBOOK)
    result = build_exact_match_allocation(source.bill, source.project)
    billed = source.bill["Total emissions kgCO2"].sum()
    allocated = result.project_emissions_exact["exact_allocated_emissions_kgco2"].sum()
    overhead = result.unallocated_bill_overhead["Total emissions kgCO2"].sum()
    assert abs((allocated + overhead) - billed) < 1e-9


@pytest.mark.skipif(not WORKBOOK.is_file(), reason=f"workbook missing: {WORKBOOK}")
def test_charts_written_from_pipeline(tmp_path: Path) -> None:
    source = load_source_data(WORKBOOK)
    allocation = build_exact_match_allocation(source.bill, source.project)
    outputs = build_output_tables(allocation, source.project)
    charts_dir = tmp_path / "charts"
    write_charts_from_output_tables(outputs, charts_dir)
    for name in CHART_FILENAMES.values():
        assert (charts_dir / name).is_file()
        assert (charts_dir / name).stat().st_size > 100
