from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

USAGE_COLORS = {
    "compute": "#2b61e5",
    "data transfer": "#0e7064",
    "storage": "#d97b06",
    "other": "#64748b",
}

PRODUCT_COLORS = {
    "grid": "#0f172a",
    "dedicated": "#2b61e5",
    "uncategorized": "#64748b",
}

FUNNEL_COLORS = ["#0B111E", "#2E6AD1", "#136F63"]
TOP10_BAR = "#136F63"

GROWTH_COLORS = ["#0D1321", "#6B7A8F", "#2E67F8", "#136D66"]
GROWTH_LABELS = ["Current", "+20% projects BAU", "Flat-emissions target", "Stretch (-10% abs.)"]

CHART_FILENAMES = {
    "usage": "footprint_by_usage_category.png",
    "product": "footprint_by_product_category.png",
    "funnel": "project_coverage_funnel.png",
    "top10": "top10_exact_mapped_projects.png",
    "region_proxy": "region_greenness_proxy.png",
    "growth": "growth_target_scenarios.png",
}


def _norm_key(s: str) -> str:
    return str(s).strip().lower()


def _usage_color(category: str) -> str:
    return USAGE_COLORS.get(_norm_key(category), "#64748b")


def _product_color(category: str) -> str:
    return PRODUCT_COLORS.get(_norm_key(category), "#64748b")


def _short_region(region: str) -> str:
    r = str(region).strip()
    if r.endswith(".platform.sh"):
        return r[: -len(".platform.sh")]
    return r.split(".")[0] if "." in r else r


def _clean_axes(ax: plt.Axes, *, grid: bool = False, grid_axis: str = "x") -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if grid:
        ax.grid(axis=grid_axis, color="#d0d0d0", linestyle="-", linewidth=0.7, alpha=0.9)
        ax.set_axisbelow(True)


def plot_footprint_by_usage(usage: pd.DataFrame, out_path: Path) -> None:
    u_lab = usage["Usage category"].astype(str).tolist()
    u_pct = usage["share_of_total"].to_numpy() * 100.0
    u_colors = [_usage_color(c) for c in u_lab]
    y = np.arange(len(u_lab))

    fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=150)
    ax.barh(y, u_pct, color=u_colors, height=0.65)
    ax.set_yticks(y, u_lab)
    ax.invert_yaxis()
    ax.set_xlabel("Share of billed emissions (%)")
    ax.set_title("Whole-bill footprint by usage category")
    ax.set_xlim(0, 40)
    ax.set_xticks(np.arange(0, 41, 5))
    _clean_axes(ax, grid=False)
    for yi, v in zip(y, u_pct):
        ax.text(v + 0.6, yi, f"{v:.1f}%", va="center", fontsize=9)

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_footprint_by_product(product: pd.DataFrame, out_path: Path) -> None:
    p_lab = product["Product category"].astype(str).tolist()
    p_pct = product["share_of_total"].to_numpy() * 100.0
    p_colors = [_product_color(c) for c in p_lab]
    yp = np.arange(len(p_lab))

    fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=150)
    ax.barh(yp, p_pct, color=p_colors, height=0.65)
    ax.set_yticks(yp, p_lab)
    ax.invert_yaxis()
    ax.set_xlabel("Share of billed emissions (%)")
    ax.set_title("Whole-bill footprint by product category")
    ax.set_xlim(0, 70)
    ax.set_xticks(np.arange(0, 71, 10))
    _clean_axes(ax, grid=False)
    for yi, v in zip(yp, p_pct):
        ax.text(v + 0.8, yi, f"{v:.1f}%", va="center", fontsize=9)

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_project_coverage_funnel(portfolio: pd.DataFrame, calc: dict[str, Any], out_path: Path) -> None:
    pmap = dict(zip(portfolio["metric"], portfolio["value"]))
    n_all = int(pmap["projects_total"])
    n_positive = int(pmap["projects_with_positive_share"])
    n_exact = int(calc["projects_with_exact_allocation"])

    labels = [
        "All projects in source",
        "Projects with >0% share",
        "Projects in exact mapped subset",
    ]
    values = [n_all, n_positive, n_exact]
    y = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(7.2, 4.5), dpi=150, facecolor="#f0f0f0")
    ax.set_facecolor("#f0f0f0")
    ax.barh(y, values, color=FUNNEL_COLORS, height=0.55)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlabel("Projects")
    ax.set_title("Project coverage funnel")
    xmax = max(values) * 1.08
    ax.set_xlim(0, max(5000, xmax))
    _clean_axes(ax, grid=True, grid_axis="x")
    for yi, v in zip(y, values):
        ax.text(v + xmax * 0.01, yi, f"{v:,}", va="center", fontsize=8, color="#333333")

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", facecolor="#f0f0f0")
    plt.close(fig)


def plot_top10_exact_mapped_projects(hotspots: pd.DataFrame, out_path: Path) -> None:
    top = hotspots.head(10).copy()
    top["label"] = top["Project"].astype(str) + " (" + top["Region"].map(_short_region) + ")"
    t_vals = top["exact_allocated_emissions_kgco2"].to_numpy() / 1000.0
    t_lab = top["label"].tolist()
    yt = np.arange(len(t_lab))

    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=150, facecolor="#f0f0f0")
    ax.set_facecolor("#f0f0f0")
    ax.barh(yt, t_vals, color=TOP10_BAR, height=0.65)
    ax.set_yticks(yt, t_lab, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Allocated emissions (tCO2)")
    ax.set_title("Top 10 exact-mapped projects")
    tmax = float(t_vals.max()) * 1.12
    ax.set_xlim(0, max(20.0, tmax))
    _clean_axes(ax, grid=True, grid_axis="x")
    for yi, v in zip(yt, t_vals):
        ax.text(v + tmax * 0.015, yi, f"{v:.1f}", va="center", fontsize=8, color="#333333")

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", facecolor="#f0f0f0")
    plt.close(fig)


def _proxy_bar_color(v: float) -> str:
    if v > 1.5:
        return "#dc2626"
    if v >= 1.0:
        return "#f59e0b"
    return "#22c55e"


def plot_region_greenness_proxy(region: pd.DataFrame, out_path: Path) -> None:
    df = region.copy()
    mat = df["is_material_customer_region"]
    if mat.dtype == object:
        mask = mat.astype(str).str.lower().isin(("true", "1", "yes"))
    else:
        mask = mat.astype(bool)
    df = df.loc[mask].copy()
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=["proxy_index_vs_material_avg"])
    df = df.sort_values("proxy_index_vs_material_avg", ascending=False)

    labels = df["Region"].map(_short_region).tolist()
    vals = df["proxy_index_vs_material_avg"].to_numpy(float)
    colors = [_proxy_bar_color(v) for v in vals]
    y = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    ax.barh(y, vals, color=colors, height=0.62)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlabel("Proxy intensity vs mapped-average = 1.0x")
    ax.set_title("Regional greenness proxy (material exact-mapped regions only)")
    ax.set_xlim(0, 2.0)
    ax.set_xticks(np.arange(0, 2.01, 0.25))
    ax.axvline(1.0, color="#9ca3af", linestyle="--", linewidth=1.0, zorder=0)
    _clean_axes(ax, grid=False)
    for yi, v in zip(y, vals):
        ax.text(v + 0.02, yi, f"{v:.2f}x", va="center", fontsize=9, color="#1f2937")

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_growth_target_scenarios(growth: pd.DataFrame, out_path: Path) -> None:
    by = growth.set_index("scenario")
    current_kg = float(by.loc["current_baseline", "total_emissions_kgco2"])
    bau_kg = float(by.loc["business_as_usual_plus_20pct_projects", "total_emissions_kgco2"])
    flat_kg = float(by.loc["flat_absolute_emissions_target", "total_emissions_kgco2"])

    heights_t = np.array([current_kg, bau_kg, flat_kg, current_kg * 0.9]) / 1000.0
    x = np.arange(4)

    fig, ax = plt.subplots(figsize=(8.5, 5), dpi=150)
    bars = ax.bar(x, heights_t, color=GROWTH_COLORS, width=0.62, edgecolor="none")
    ax.set_xticks(x, GROWTH_LABELS, rotation=0, fontsize=9)
    ax.set_ylabel("Total emissions (tCO2)")
    ax.set_title("Growth target scenarios")
    ymax = float(heights_t.max()) * 1.18
    ax.set_ylim(0, ymax)
    top_tick = max(1000, int(np.ceil(ymax / 200) * 200))
    ax.set_yticks(np.arange(0, top_tick + 1, 200))
    _clean_axes(ax, grid=False)

    for bar, h in zip(bars, heights_t):
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            h + ymax * 0.02,
            f"{round(h):,}t".replace(",", ""),
            ha="center",
            va="bottom",
            fontsize=9,
            color="#1f2937",
        )

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def write_charts_from_output_tables(output_tables: dict[str, Any], charts_dir: str | Path) -> None:
    charts_dir = Path(charts_dir)
    charts_dir.mkdir(parents=True, exist_ok=True)

    usage = output_tables["usage_mix"]
    product = output_tables["product_mix"]
    portfolio = output_tables["portfolio_summary"]
    calc = output_tables["calculation_summary"]
    hotspots = output_tables["project_hotspots"]
    growth = output_tables["growth_targets"]
    region = output_tables["region_proxy_intensity"]

    plot_footprint_by_usage(usage, charts_dir / CHART_FILENAMES["usage"])
    plot_footprint_by_product(product, charts_dir / CHART_FILENAMES["product"])
    plot_project_coverage_funnel(portfolio, calc, charts_dir / CHART_FILENAMES["funnel"])
    plot_top10_exact_mapped_projects(hotspots, charts_dir / CHART_FILENAMES["top10"])
    plot_region_greenness_proxy(region, charts_dir / CHART_FILENAMES["region_proxy"])
    plot_growth_target_scenarios(growth, charts_dir / CHART_FILENAMES["growth"])


def read_output_tables_for_charts(inputs_dir: str | Path) -> dict[str, Any]:
    inputs_dir = Path(inputs_dir)
    with open(inputs_dir / "calculation_summary.json", encoding="utf-8") as f:
        calc = json.load(f)
    return {
        "usage_mix": pd.read_csv(inputs_dir / "usage_mix.csv"),
        "product_mix": pd.read_csv(inputs_dir / "product_mix.csv"),
        "portfolio_summary": pd.read_csv(inputs_dir / "portfolio_summary.csv"),
        "calculation_summary": calc,
        "project_hotspots": pd.read_csv(inputs_dir / "project_hotspots.csv"),
        "growth_targets": pd.read_csv(inputs_dir / "growth_targets.csv"),
        "region_proxy_intensity": pd.read_csv(inputs_dir / "region_proxy_intensity.csv"),
    }


def write_charts_from_disk(inputs_dir: str | Path, charts_dir: str | Path) -> None:
    tables = read_output_tables_for_charts(inputs_dir)
    write_charts_from_output_tables(tables, charts_dir)
