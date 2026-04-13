from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from co2_case.charts import write_charts_from_disk


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--inputs-dir",
        type=Path,
        default=PROJECT_ROOT / "outputs",
        help="Metrics output directory.",
    )
    p.add_argument(
        "--charts-dir",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "charts",
        help="Chart output directory.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    inputs = args.inputs_dir.resolve()
    charts = args.charts_dir.resolve()

    required = [
        "usage_mix.csv",
        "product_mix.csv",
        "project_hotspots.csv",
        "growth_targets.csv",
        "portfolio_summary.csv",
        "calculation_summary.json",
        "region_proxy_intensity.csv",
    ]
    missing = [f for f in required if not (inputs / f).exists()]
    if missing:
        raise SystemExit(f"Missing files in {inputs}: {missing}")

    write_charts_from_disk(inputs, charts)
    print(f"Wrote charts to {charts}")


if __name__ == "__main__":
    main()
