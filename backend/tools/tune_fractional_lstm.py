"""Run the bounded pre-2016 LSTM search without a full historical backtest."""

import argparse
from datetime import date
import logging
from pathlib import Path

from config.settings import STOCKS_DATABASE_PATH
from research.fractional_tuning import SearchSettings, run_search
from research.experiment_runs import tracked_run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=Path(STOCKS_DATABASE_PATH))
    parser.add_argument('--directory', type=Path, help='Default: search inside a new numbered run')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--stocks', type=int, default=6)
    parser.add_argument('--trials', type=int, default=20, help='Total across both methods')
    parser.add_argument('--max-epochs', type=int, default=120)
    parser.add_argument('--patience', type=int, default=15)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--test-start', type=date.fromisoformat, default=date(2016, 10, 14))
    args = parser.parse_args()
    if args.resume and args.directory is None:
        parser.error('--resume requires the original --directory')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    artifact = args.directory / 'report.json' if args.directory is not None else None
    with tracked_run('fractional-search', artifact, resume=args.resume) as experiment:
        args.directory = experiment.artifact.parent
        logging.info('Experiment ID: %s (%s)', experiment.run_id, experiment.directory)
        report = run_search(
            args.database, args.directory, SearchSettings(
                stock_count=args.stocks, total_trials=args.trials, max_epochs=args.max_epochs,
                patience=args.patience, seed=args.seed,
            ), test_start=args.test_start, resume=args.resume,
        )
        experiment.metadata['parameters'] = report['parameters']
        experiment.metadata['data_provenance'] = report['data_provenance']
        for method, result in report['methods'].items():
            logging.info('%s selected=%s relative_MAE=%.4f qualified=%s',
                         method, result['selected_trial'], result['relative_mae'],
                         result['qualified_vs_zero_baseline'])
        logging.info('Verified report: %s', args.directory / 'report.json')


if __name__ == '__main__':
    main()
