from __future__ import annotations

import pandas as pd

from .config import ColumnNames

C = ColumnNames()


def _normalize_string_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = (
                df[column]
                .astype('string')
                .fillna('')
.str.strip()
            )
    return df


def clean_bill_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = _normalize_string_columns(
        df,
        [C.provider, C.sku, C.product_category, C.usage_category],
    )
    df[C.total_emissions_kg] = pd.to_numeric(df[C.total_emissions_kg], errors='raise')
    df['bill_key_provider_sku'] = df[C.provider] + ' || ' + df[C.sku]
    df['bill_key_full_grain'] = (
        df[C.provider] + ' || ' + df[C.sku] + ' || ' + df[C.product_category] + ' || ' + df[C.usage_category]
    )
    return df


def clean_project_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = _normalize_string_columns(
        df,
        [C.provider, C.sku, C.project, C.region],
    )
    df[C.project_share] = pd.to_numeric(df[C.project_share], errors='raise')
    df['project_key_provider_sku'] = df[C.provider] + ' || ' + df[C.sku]
    return df
