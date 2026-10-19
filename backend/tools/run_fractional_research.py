"""Run the database-backed Shanghai-stock LSTM research experiment."""

import argparse
from datetime import date
import json
from pathlib import Path

from config.settings import STOCKS_DATABASE_PATH
from research.database_fractional import load_fractional_database
from research.fractional_forecast import (
    DifferencingError, ForecastConfig, simulate_long_only,
)
from research.fractional_lstm import LSTMTrial, train_stock


def run(args) -> dict:
    config = ForecastConfig(
        train_start=args.train_start, validation_start=args.validation_start,
        test_start=args.test_start, test_end=args.test_end,
    )
    config.validate()
    if args.output.exists():
        raise DifferencingError('Refusing to overwrite an existing experiment')
    prices, universe, provenance = load_fractional_database(
        args.database, config, seed=args.seed, universe_size=args.universe_size,
    )
    candidates = universe.members_between(config.test_start, config.test_end)
    models = {}
    predictions = {'de_prado': {}, 'log_return': {}}
    trial_settings = [LSTMTrial(hidden_size=size, epochs=args.epochs) for size in (16, 32)]
    for symbol in candidates:
        stock = prices[prices['instrument'] == symbol]
        for method in predictions:
            print(f'Training {symbol} {method} using pre-test data', flush=True)
            metadata, forecasts = train_stock(stock, config, method, trial_settings)
            models[f'{symbol}:{method}'] = metadata
            predictions[method].update(forecasts)

    runs = {}
    for method, forecasts in predictions.items():
        signal_days = sorted({
            day for day in prices['date'] if config.test_start <= day <= config.test_end
        })[:-1]
        gaps = [
            (day.isoformat(), symbol) for day in signal_days for symbol in candidates
            if (day, symbol) not in forecasts
        ]
        if gaps:
            raise DifferencingError(
                f'{method} lacks forecast coverage: {len(gaps)} gaps, first {gaps[:5]}',
            )
        runs[method] = simulate_long_only(
            prices, forecasts, universe, config.test_start, config.test_end,
            initial_capital=args.capital, buy_cost=args.buy_cost,
            sell_cost=args.sell_cost, signal_threshold=args.signal_threshold,
        )
    runs['database_random_equal_slot'] = simulate_long_only(
        prices, {}, universe, config.test_start, config.test_end,
        initial_capital=args.capital, buy_cost=args.buy_cost,
        sell_cost=args.sell_cost, signal_threshold=args.signal_threshold,
        benchmark=True,
    )
    return {
        'paper': 'https://arxiv.org/abs/2505.19243',
        'status': 'method_migration_not_exact_replication',
        'universe': (
            f"Seeded random sample of {args.universe_size} complete-history "
            f"Shanghai non-ETF stocks from stocks.db; survivorship biased, not SSE50."
        ),
        'data_provenance': provenance,
        'inputs': {'database': provenance},
        'parameters': {
            'train_start': config.train_start.isoformat(),
            'validation_start': config.validation_start.isoformat(),
            'test_start': config.test_start.isoformat(),
            'test_end': config.test_end.isoformat(),
            'seed': args.seed,
            'universe_size': args.universe_size,
            'buy_cost': args.buy_cost,
            'sell_cost': args.sell_cost,
            'signal_threshold': args.signal_threshold,
            'initial_capital': args.capital,
        },
        'models': models,
        'backtests': runs,
        'deviations': [
            'A seeded sample from the database replaces historical SSE50 membership; the sample has survivorship bias.',
            'Database adjusted-close ratios are applied to OHLC prices.',
            'De Prado and first-difference branches only; no ARFIMA/ARTFIMA R estimator replication.',
            'ADF grid 0.05, truncation 0.001, AIC lag selection are disclosed implementation settings.',
            'Single-layer CPU PyTorch LSTM; hidden16/32, best validation epoch, no test-time fitting.',
            'Training, validation and test dates are recorded in parameters.',
            'Daily equal allocation slots; no reallocation of inactive slots, 95% max exposure.',
            'Research costs cannot replace actual A-share commissions or execution rules.',
            'Only a research simulator; actual stock execution must be validated separately.',
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--database', type=Path, default=STOCKS_DATABASE_PATH,
        help='Read-only stocks.db path',
    )
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--universe-size', type=int, default=30)
    parser.add_argument('--train-start', type=date.fromisoformat, default=date(2014, 1, 1))
    parser.add_argument('--validation-start', type=date.fromisoformat, default=date(2022, 4, 1))
    parser.add_argument('--test-start', type=date.fromisoformat, default=date(2024, 4, 1))
    parser.add_argument('--test-end', type=date.fromisoformat, default=date(2026, 4, 30))
    parser.add_argument('--capital', type=float, default=100000)
    parser.add_argument('--epochs', type=int, default=30)
    parser.add_argument('--buy-cost', type=float, default=0.0005)
    parser.add_argument('--sell-cost', type=float, default=0.001)
    parser.add_argument('--signal-threshold', type=float, default=0.002)
    args = parser.parse_args()
    try:
        result = run(args)
        with args.output.open('x', encoding='utf-8') as output:
            json.dump(result, output, ensure_ascii=False, allow_nan=False, indent=2)
    except (OSError, ValueError, ImportError) as exc:
        parser.exit(1, f'Research stopped: {exc}\n')
    print(f'Research result: {args.output}')


if __name__ == '__main__':
    main()
