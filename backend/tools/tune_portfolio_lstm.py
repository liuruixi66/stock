"""Run the approved 20-trial shared-LSTM portfolio search."""

import argparse
import json
import logging
from pathlib import Path

from config.settings import STOCKS_DATABASE_PATH
from research.experiment_runs import tracked_run
from research.fractional_tuning import atomic_json
from research.portfolio_tuning import (
    PortfolioSearchSettings, run_portfolio_search,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=Path(STOCKS_DATABASE_PATH))
    parser.add_argument('--universe', type=Path, required=True)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, help='Default: a new numbered portfolio-search run')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    try:
        universe_path = args.universe.resolve()
        audit_path = args.audit.resolve()
        with universe_path.open('r', encoding='utf-8') as stream:
            universe = json.load(stream)
        with audit_path.open('r', encoding='utf-8') as stream:
            audit = json.load(stream)
        if (audit.get('status') != 'passed'
                or audit.get('universe_signature') != universe.get('signature')):
            raise ValueError('History audit must pass for the exact frozen universe signature')
        artifact = args.output.resolve() if args.output else None
        if artifact is not None and artifact.exists():
            raise ValueError(f'Refusing to overwrite search output: {artifact}')
        with tracked_run('portfolio-search', artifact) as experiment:
            report = run_portfolio_search(
                args.database, universe_path,
                experiment.directory / 'search', PortfolioSearchSettings(),
            )
            report['run_id'] = experiment.run_id
            report['audit_file'] = str(audit_path)
            report['audit_status'] = audit['status']
            atomic_json(experiment.artifact, report)
            experiment.metadata.update(
                universe_signature=universe['signature'],
                audit_file=str(audit_path),
                parameters=report['settings'],
                selected_method=report.get('selected_method'),
                search_qualified=report.get('search_qualified', False),
            )
            logging.info(
                'Portfolio search %s: qualified=%s, selected_method=%s, report=%s',
                experiment.run_id, report.get('search_qualified'),
                report.get('selected_method'), experiment.artifact,
            )
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f'Portfolio search failed: {exc}\n')


if __name__ == '__main__':
    main()
