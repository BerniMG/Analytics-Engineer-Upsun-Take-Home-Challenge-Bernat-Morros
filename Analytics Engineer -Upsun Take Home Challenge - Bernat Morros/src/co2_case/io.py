from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .cleaning import clean_bill_df, clean_project_df
from .config import BILL_REQUIRED_COLUMNS, PROJECT_REQUIRED_COLUMNS

logger = logging.getLogger(__name__)


@dataclass
class SourceData:
    bill: pd.DataFrame
    project: pd.DataFrame
    bill_csv: pd.DataFrame | None = None
    project_csv: pd.DataFrame | None = None
    source_notes: dict | None = None


def _require_columns(df: pd.DataFrame, required: list[str], label: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{label} is missing required columns: {missing}")


def _parse_percent_string(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.strip().str.rstrip('%')
    return pd.to_numeric(cleaned, errors='coerce') / 100.0


def load_source_data(
    workbook_path: str | Path,
    bill_csv_path: str | Path | None = None,
    project_csv_path: str | Path | None = None,
) -> SourceData:
    """Load workbook tabs and optionally cross-check rounded CSV exports.

    The workbook is used as the numeric source of truth because the project shares
    remain full precision there and sum to ~1.0 exactly.
    """
    workbook_path = Path(workbook_path)
    bill = pd.read_excel(workbook_path, sheet_name='SKUs')
    project = pd.read_excel(workbook_path, sheet_name='Projects')

    _require_columns(bill, BILL_REQUIRED_COLUMNS, 'Workbook SKUs sheet')
    _require_columns(project, PROJECT_REQUIRED_COLUMNS, 'Workbook Projects sheet')

    bill = clean_bill_df(bill)
    project = clean_project_df(project)

    notes: dict[str, float | str] = {
        'numeric_source_of_truth': str(workbook_path),
        'workbook_bill_total_kg': float(bill['Total emissions kgCO2'].sum()),
        'workbook_project_share_total': float(project['Emissions kgCO2 % of total emissions'].sum()),
    }

    bill_csv = None
    project_csv = None

    if bill_csv_path is not None:
        bill_csv = pd.read_csv(bill_csv_path)
        _require_columns(bill_csv, BILL_REQUIRED_COLUMNS, 'Bill CSV')
        bill_csv = clean_bill_df(bill_csv)
        notes['bill_csv_total_kg'] = float(bill_csv['Total emissions kgCO2'].sum())
        notes['bill_csv_delta_vs_workbook_kg'] = float(notes['bill_csv_total_kg'] - notes['workbook_bill_total_kg'])

    if project_csv_path is not None:
        project_csv = pd.read_csv(project_csv_path)
        _require_columns(project_csv, PROJECT_REQUIRED_COLUMNS, 'Project CSV')
        project_csv[PROJECT_REQUIRED_COLUMNS[-1]] = _parse_percent_string(project_csv[PROJECT_REQUIRED_COLUMNS[-1]])
        project_csv = clean_project_df(project_csv)
        notes['project_csv_share_total'] = float(project_csv['Emissions kgCO2 % of total emissions'].sum())
        notes['project_csv_delta_vs_workbook_share'] = float(
            notes['project_csv_share_total'] - notes['workbook_project_share_total']
        )

    logger.info('Loaded workbook and optional CSV cross-checks')
    return SourceData(
        bill=bill,
        project=project,
        bill_csv=bill_csv,
        project_csv=project_csv,
        source_notes=notes,
    )
