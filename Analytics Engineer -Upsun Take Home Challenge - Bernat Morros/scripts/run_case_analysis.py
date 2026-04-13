from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from co2_case.charts import write_charts_from_output_tables
from co2_case.io import load_source_data
from co2_case.modeling import build_exact_match_allocation
from co2_case.metrics import build_output_tables, write_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run the refined CO2 allocation case analysis.')
    parser.add_argument('--workbook', required=True, help='Path to the source workbook.')
    parser.add_argument('--bill-csv', help='Optional path to the bill CSV export.')
    parser.add_argument('--project-csv', help='Optional path to the project CSV export.')
    parser.add_argument('--output-dir', required=True, help='Directory where outputs will be written.')
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    args = parse_args()

    source_data = load_source_data(
        workbook_path=args.workbook,
        bill_csv_path=args.bill_csv,
        project_csv_path=args.project_csv,
    )
    allocation = build_exact_match_allocation(source_data.bill, source_data.project)
    outputs = build_output_tables(allocation, source_data.project)
    outputs['source_notes'] = source_data.source_notes or {}
    write_outputs(outputs, args.output_dir)
    charts_dir = Path(args.output_dir) / 'charts'
    write_charts_from_output_tables(outputs, charts_dir)
    logging.info('Outputs written to %s', args.output_dir)
    logging.info('Charts written to %s', charts_dir)


if __name__ == '__main__':
    main()
