"""Audit the whole frozen industry universe without training or altering market data."""

import argparse
from datetime import date
import json
import logging
from pathlib import Path

from market_data.portfolio_history import (
    PortfolioHistoryError, load_portfolio_history, portfolio_price_contract,
)
from research.fractional_tuning import atomic_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('universe', type=Path)
    parser.add_argument('--database', type=Path, help='Default: frozen universe database path')
    parser.add_argument('--start', type=date.fromisoformat, default=date(2006, 10, 16))
    parser.add_argument('--end', type=date.fromisoformat, default=date(2026, 10, 14))
    parser.add_argument('--output', type=Path, required=True, help='New audit JSON; refuses overwrite')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    try:
        if args.output.exists():
            raise ValueError('Refusing to overwrite an existing audit')
        universe = json.loads(args.universe.read_text(encoding='utf-8'))
        database = args.database or Path(universe['database'])
        try:
            _, _, _, provenance = load_portfolio_history(database, universe, args.start, args.end)
        except PortfolioHistoryError as exc:
            report = {
                'status': 'blocked', 'universe_signature': universe['signature'],
                'price_contract': portfolio_price_contract(), 'database': str(database.resolve()),
                'start': args.start.isoformat(), 'end': args.end.isoformat(),
                'issues': exc.issues, 'training_started': False,
            }
        else:
            report = {'status': 'passed', **provenance, 'training_started': False}
        atomic_json(args.output, report)
        persisted = json.loads(args.output.read_text(encoding='utf-8'))
        if persisted != report:
            raise ValueError('Saved history audit differs from computed report')
        logging.info('History audit %s: %s', report['status'], args.output)
        if report['status'] == 'blocked':
            parser.exit(2, f'History audit blocked by {len(report["issues"])} issue(s); see {args.output}\n')
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f'History audit failed: {exc}\n')


if __name__ == '__main__':
    main()
