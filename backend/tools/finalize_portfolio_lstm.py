"""Refit the selected portfolio model and run the fixed 2016-2026 re-evaluation."""

import argparse
import json
import logging
from pathlib import Path

from config.settings import STOCKS_DATABASE_PATH
from research.experiment_runs import tracked_run
from research.fractional_tuning import atomic_json
from research.portfolio_finalization import finalize_portfolio_search


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=Path(STOCKS_DATABASE_PATH))
    parser.add_argument('--universe', type=Path, required=True)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--search-run', type=Path, required=True,
                        help='Completed portfolio-search run directory')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    args = parser.parse_args()
    try:
        search_directory = args.search_run.resolve()
    except (OSError, ValueError) as exc:
        parser.exit(1, f'Invalid search run path: {exc}\n')
    run_file = search_directory / 'run.json'
    search_report_path = search_directory / 'results.json'
    try:
        with run_file.open('r', encoding='utf-8') as stream:
            search_run = json.load(stream)
        with search_report_path.open('r', encoding='utf-8') as stream:
            search_report = json.load(stream)
        if (search_run.get('status') != 'completed'
                or search_run.get('kind') != 'portfolio-search'
                or search_run.get('run_id') != search_report.get('run_id')
                or search_report.get('search_qualified') is not True):
            raise ValueError('Finalization requires a completed, qualified portfolio search')
        with tracked_run('portfolio-training') as experiment:
            report = finalize_portfolio_search(
                args.database,
                args.universe,
                args.audit,
                search_report_path,
                experiment.directory,
            )
            report['run_id'] = experiment.run_id
            report['search_run_id'] = search_run['run_id']
            report['audit_file'] = str(args.audit.resolve())
            atomic_json(experiment.artifact, report)
            experiment.metadata.update(
                parent_search_run_id=search_run['run_id'],
                selected_method=report['selected_method'],
                selected_trial=report['selected_trial'],
                model_bundle=report['final_refit']['model_bundle'],
                historical_drawdown_gate_passed=report['historical_drawdown_gate_passed'],
                live_trading_eligible=False,
            )
            logging.info(
                'Finalization %s: method=%s trial=%s history_return=%.4f drawdown=%.4f bundle=%s',
                experiment.run_id, report['selected_method'], report['selected_trial'],
                report['historical_re_evaluation']['portfolio_return'],
                report['historical_re_evaluation']['max_drawdown'],
                report['final_refit']['model_bundle'],
            )
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f'Portfolio finalization failed: {exc}\n')


if __name__ == '__main__':
    main()
