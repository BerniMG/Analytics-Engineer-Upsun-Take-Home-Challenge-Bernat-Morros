# Analytics Engineer - Take Home Challenge - Bernat Morros

This package contains the cleaning, auditing and allocation code used for the refined take-home solution.

## What this package does

1. Loads the uploaded Excel workbook as the **numeric source of truth**.
2. Cross-checks the CSV exports and documents the rounding differences.
3. Audits the real source grain before any allocation.
4. Builds a **conservative exact-match allocation** using `provider + SKU Description` as the only bridge key shared by both files.
5. Preserves bill-side `Product category` and `Usage category` on the allocated facts.
6. Keeps unmatched billed emissions as **shared / unallocated overhead** instead of forcing low-confidence project assignments.
7. Produces reproducible output tables that back the presentation.

## Why the logic is conservative

- The bill table is not unique at SKU text alone.
- The effective bill grain is `provider + SKU Description + Product category + Usage category`.
- The project file does **not** contain product category or usage category.
- Therefore the only exact shared key across both files is `provider + SKU Description`.

This package intentionally avoids inventing additional mapping rules that the input data cannot support exactly.

## Project structure

- `src/co2_case/` — Python package (load, clean, allocate, metrics, chart export).
- `src/co2_case/sql/` — **dbt** project: a representation of how the same logic would layer in BigQuery (staging → intermediate → marts). It is not executed by the Python pipeline; wire it to `raw` sources and a profile when you run dbt locally.
- `scripts/run_case_analysis.py` — end-to-end run: tables under `outputs/` plus PNGs under `outputs/charts/`.
- `scripts/plot_metrics_charts.py` — optional: rebuild charts from existing CSV/JSON only.
- `sources/xlsx/` — place the workbook here (ignored by git).
- `outputs/` — generated CSV, JSON, and chart images.
- `tests/` — reconciliation and chart smoke checks (`pip install -e ".[dev]"` for pytest).

## How to run

```bash
pip install -e .
python scripts/run_case_analysis.py --workbook sources/xlsx/AE_Take_home_challenge.xlsx --output-dir outputs
```

Optional CSV cross-checks: `--bill-csv … --project-csv …`. dbt: `cd src/co2_case/sql && dbt deps && dbt run` (after configuring sources and `profiles.yml`).

## Main output tables

- `source_audit.json`, `source_notes.json`, `calculation_summary.json`
- `portfolio_summary.csv`, `usage_mix.csv`, `product_mix.csv`, `usage_coverage.csv`, `product_coverage.csv`
- `project_hotspots.csv`, `region_proxy_intensity.csv`, `growth_targets.csv`, `reduction_levers.csv`
- `project_emissions_exact.csv`, `unallocated_bill_overhead.csv`
- PNGs in `outputs/charts/` (usage/product footprint, funnel, top 10, region proxy, growth scenarios)

## Quality checks built into the pipeline

- required columns present
- workbook totals reconcile
- project shares sum to ~1.0
- allocated + unallocated = billed total
- region is stable at project level

## Notes on interpretation

- Region "greenness" is a **proxy index**, not a physical engineering efficiency measure, because the sample lacks raw usage units like GB or compute hours.
- Coverage metrics should always be read alongside the shared-overhead amount.
