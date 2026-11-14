"""Freeze five same-day market-cap leaders per local industry without training."""

import argparse
import csv
from datetime import date
import json
import logging
from pathlib import Path

from config.runtime import STOCKS_DATABASE_PATH
from market_data.industry_universe import (
    exclude_universe_instruments, select_industry_leaders, verify_industry_universe,
)
from research.experiment_runs import tracked_run
from research.fractional_tuning import atomic_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=Path(STOCKS_DATABASE_PATH))
    parser.add_argument('--market-cap-date', type=date.fromisoformat,
                        help='One completed trading date; default: latest date in daily_basic')
    parser.add_argument('--per-industry', type=int, default=5)
    parser.add_argument('--output', type=Path, help='Default: a new numbered universe run')
    parser.add_argument(
        '--exclude-instrument', action='append', default=[],
        metavar='CODE', help='Explicitly remove a selected instrument without industry backfill',
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    try:
        if args.output is not None and args.output.exists():
            raise ValueError('Refusing to overwrite an existing universe')
        with tracked_run('portfolio-universe', args.output) as run:
            report = select_industry_leaders(
                args.database, per_industry=args.per_industry, market_cap_date=args.market_cap_date,
            )
            if args.exclude_instrument:
                report = exclude_universe_instruments(
                    report,
                    {symbol: 'user_excluded_historical_data_gaps'
                     for symbol in args.exclude_instrument},
                )
            atomic_json(run.artifact, report)
            csv_path = run.directory / 'industry-leaders.csv'
            with csv_path.open('x', encoding='utf-8-sig', newline='') as stream:
                columns = ['industry', 'industry_rank', 'instrument', 'name',
                           'total_market_cap', 'market_cap_date', 'industry_snapshot_at']
                writer = csv.DictWriter(stream, fieldnames=columns, extrasaction='ignore')
                writer.writeheader()
                for stocks in report['industries'].values():
                    for stock in stocks:
                        writer.writerow({**stock, 'market_cap_date': report['market_cap_date']})
            verify_industry_universe(json.loads(run.artifact.read_text(encoding='utf-8')))
            with csv_path.open(encoding='utf-8-sig', newline='') as stream:
                saved = sorted(row['instrument'] for row in csv.DictReader(stream))
            if saved != report['selected_instruments']:
                raise ValueError('Saved CSV does not match the frozen universe')
            run.metadata.update(
                universe_signature=report['signature'], stock_count=report['stock_count'],
                industry_count=report['industry_count'], csv_path=str(csv_path),
                market_cap_date=report['market_cap_date'],
            )
            logging.info('Universe %s: %s; CSV: %s', run.run_id, run.artifact, csv_path)
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Industry selection failed: {exc}\n')


if __name__ == '__main__':
    main()
