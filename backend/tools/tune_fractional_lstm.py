"""Run the bounded pre-2016 LSTM search without a full historical backtest."""

import argparse
from datetime import date
import logging
from pathlib import Path

from config.settings import STOCKS_DATABASE_PATH
from research.fractional_tuning import SearchSettings, run_search


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=Path(STOCKS_DATABASE_PATH))
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--stocks', type=int, default=6)
    parser.add_argument('--trials', type=int, default=20, help='Total across both methods')
    parser.add_argument('--max-epochs', type=int, default=120)
    parser.add_argument('--patience', type=int, default=15)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--test-start', type=date.fromisoformat, default=date(2016, 10, 14))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    report = run_search(
        args.database, args.directory, SearchSettings(
            stock_count=args.stocks, total_trials=args.trials, max_epochs=args.max_epochs,
            patience=args.patience, seed=args.seed,
        ), test_start=args.test_start, resume=args.resume,
    )
    for method, result in report['methods'].items():
        logging.info('%s selected=%s relative_MAE=%.4f qualified=%s',
                     method, result['selected_trial'], result['relative_mae'],
                     result['qualified_vs_zero_baseline'])
    logging.info('Verified report: %s', args.directory / 'report.json')


if __name__ == '__main__':
    main()
