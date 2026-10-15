"""Offline SSE50 top30 research. Run from backend with -m tools.run_fractional_research."""

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path

import pandas as pd

from research.fractional_forecast import (
    DifferencingError, FixedRandomThirty, ForecastConfig, HistoricalTopThirty,
    simulate_long_only, validate_prices,
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
    provenance = json.loads(args.metadata.read_text(encoding='utf-8'))
    universe_path = args.fixed_universe if args.fixed_universe else args.weights
    hash_key = 'fixed_universe_sha256' if args.fixed_universe else 'weights_sha256'
    valid_adjustment = (
        provenance.get('adjustment') == 'hfq' and bool(provenance.get('source'))
    ) or (
        provenance.get('adjustment') == 'yahoo_adjclose_ratio'
        and provenance.get('source') == 'yahoo.chart'
    )
    if (not valid_adjustment
            or provenance.get('prices_sha256') != hashlib.sha256(args.prices.read_bytes()).hexdigest()
            or provenance.get(hash_key) != hashlib.sha256(universe_path.read_bytes()).hexdigest()):
        raise DifferencingError('Require declared supported adjustment/source and matching data hashes')
    prices = validate_prices(pd.read_csv(args.prices))
    universe = (FixedRandomThirty(json.loads(universe_path.read_text(encoding='utf-8')))
                if args.fixed_universe else HistoricalTopThirty(pd.read_csv(universe_path)))
    candidates = universe.members_between(config.test_start, config.test_end)
    missing = sorted(set(candidates) - set(prices['instrument']))
    if missing:
        raise DifferencingError(f'Prices missing for historical members: {missing}')
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
            (day.isoformat(), symbol) for day in signal_days for symbol in universe.at(day)[1]
            if (day, symbol) not in forecasts
        ]
        if gaps:
            raise DifferencingError(f'{method} lacks forecast coverage: {len(gaps)} gaps, first {gaps[:5]}')
        runs[method] = simulate_long_only(
            prices, forecasts, universe, config.test_start, config.test_end,
            initial_capital=args.capital, buy_cost=args.buy_cost, sell_cost=args.sell_cost,
            signal_threshold=args.signal_threshold,
        )
    runs['fixed_random30_equal_slot' if args.fixed_universe else 'historical_top30_equal_slot'] = simulate_long_only(
        prices, {}, universe, config.test_start, config.test_end,
        initial_capital=args.capital, buy_cost=args.buy_cost, sell_cost=args.sell_cost,
        signal_threshold=args.signal_threshold, benchmark=True,
    )
    return {
        'paper': 'https://arxiv.org/abs/2505.19243',
        'status': 'method_migration_not_exact_replication',
        'universe': ('000016.SHI current random30; SURVIVORSHIP BIASED, not historical top30'
                     if args.fixed_universe else
                     '000016.SHI historical weight top30, snapshot strictly before signal'),
        'data_provenance': provenance,
        'inputs': {
            name: {'path': str(path.resolve()), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            for name, path in [('prices', args.prices), ('universe', universe_path)]
        },
        'parameters': {
            'test_start': config.test_start.isoformat(), 'test_end': config.test_end.isoformat(),
            'buy_cost': args.buy_cost, 'sell_cost': args.sell_cost,
            'signal_threshold': args.signal_threshold, 'initial_capital': args.capital,
        },
        'models': models, 'backtests': runs,
        'deviations': [
            'SSE50 stocks rather than the four overseas indices in the paper.',
            'De Prado and first-difference branches only; no ARFIMA/ARTFIMA R estimator replication.',
            'ADF grid 0.05, truncation 0.001, AIC lag selection are disclosed implementation settings.',
            'Single-layer CPU PyTorch LSTM; hidden16/32, best validation epoch, no test-time fitting.',
            'Training 2014-2022Q1, validation 2022Q2-2024Q1, test 2024Q2-2026Apr.',
            'SMA RSI Bollinger and MACD calculation conventions recorded in source.',
            'Daily 30 equal allocation slots; no reallocation of inactive slots, 95% max exposure.',
            'Costs differ from paper 0.005%; research costs cannot replace actual A-share commissions.',
            'Only a research simulator; actual stock execution must be validated in BigQuant.',
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prices', type=Path, required=True, help='Adjusted OHLCV CSV, training + test')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--weights', type=Path, help='Complete historical SSE50 snapshots CSV')
    group.add_argument('--fixed-universe', type=Path, help='Exploratory current random30 JSON')
    parser.add_argument('--metadata', type=Path, required=True, help='Source, hfq adjustment and data SHA256 JSON')
    parser.add_argument('--output', type=Path, required=True)
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
