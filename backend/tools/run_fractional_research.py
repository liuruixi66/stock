"""Run the database-backed Shanghai-stock LSTM research experiment."""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import ExitStack
from datetime import date
import hashlib
import json
import logging
import math
import os
from pathlib import Path

from config.settings import STOCKS_DATABASE_PATH
from research.database_fractional import load_fractional_database
from research.fractional_forecast import (
    DifferencingError, ForecastConfig, simulate_long_only,
)
from research.fractional_lstm import LSTMTrial, train_stock
from research.fractional_results import chinese_result


CHECKPOINT_VERSION = 1
METHODS = ('de_prado', 'log_return')


def _checkpoint_signature(args) -> str:
    database = args.database.expanduser().resolve()
    stat = database.stat()
    parameters = {
        'database': str(database),
        'database_size': stat.st_size,
        'database_mtime_ns': stat.st_mtime_ns,
        'seed': args.seed,
        'universe_size': args.universe_size,
        'train_start': args.train_start.isoformat(),
        'validation_start': args.validation_start.isoformat(),
        'test_start': args.test_start.isoformat(),
        'test_end': args.test_end.isoformat(),
        'walk_forward_validation_days': args.walk_forward_validation_days,
        'epochs': args.epochs,
        'capital': args.capital,
        'buy_cost': args.buy_cost,
        'sell_cost': args.sell_cost,
        'signal_threshold': args.signal_threshold,
        'model_seed': 42,
        'methods': METHODS,
        'hidden_sizes': (16, 32),
    }
    serialized = json.dumps(parameters, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _checkpoint_path(output: Path) -> Path:
    return output.with_name(output.name + '.progress.jsonl')


def _restore_checkpoint(path: Path, signature: str):
    models = {}
    predictions = {method: {} for method in METHODS}
    completed = set()
    if not path.exists():
        with path.open('x', encoding='utf-8') as checkpoint:
            checkpoint.write(json.dumps({
                'type': 'header', 'version': CHECKPOINT_VERSION,
                'signature': signature,
            }, separators=(',', ':')) + '\n')
            checkpoint.flush()
            os.fsync(checkpoint.fileno())
        return models, predictions, completed

    with path.open('r', encoding='utf-8') as checkpoint:
        first_line = checkpoint.readline()
        try:
            header = json.loads(first_line)
        except json.JSONDecodeError as exc:
            raise DifferencingError(f'Invalid checkpoint header in {path}') from exc
        if (header.get('type') != 'header'
                or header.get('version') != CHECKPOINT_VERSION
                or header.get('signature') != signature):
            raise DifferencingError(
                f'Checkpoint does not match this experiment: {path}',
            )
        for line_number, line in enumerate(checkpoint, start=2):
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                raise DifferencingError(
                    f'Invalid checkpoint record at {path}:{line_number}',
                ) from exc
            symbol = entry.get('symbol')
            method_results = entry.get('methods')
            if (entry.get('type') != 'stock' or not isinstance(symbol, str)
                    or not symbol or symbol in completed
                    or not isinstance(method_results, dict)
                    or set(method_results) != set(METHODS)):
                raise DifferencingError(
                    f'Invalid or duplicate stock checkpoint at {path}:{line_number}',
                )
            for method in METHODS:
                result = method_results[method]
                if not isinstance(result.get('metadata'), dict):
                    raise DifferencingError(
                        f'Missing model metadata at {path}:{line_number}',
                    )
                models[f'{symbol}:{method}'] = result['metadata']
                for item in result.get('forecasts', []):
                    day = date.fromisoformat(item['date'])
                    forecast_symbol = item['instrument']
                    value = float(item['predicted_return'])
                    if forecast_symbol != symbol or not math.isfinite(value):
                        raise DifferencingError(
                            f'Invalid forecast in checkpoint at {path}:{line_number}',
                        )
                    predictions[method][(day, symbol)] = value
            completed.add(symbol)
    return models, predictions, completed


def _append_checkpoint(path: Path, symbol: str, method_results: dict) -> None:
    entry = {
        'type': 'stock',
        'symbol': symbol,
        'methods': {
            method: {
                'metadata': metadata,
                'forecasts': [
                    {
                        'date': day.isoformat(),
                        'instrument': forecast_symbol,
                        'predicted_return': value,
                    }
                    for (day, forecast_symbol), value in sorted(forecasts.items())
                ],
            }
            for method, (metadata, forecasts) in method_results.items()
        },
    }
    with path.open('a', encoding='utf-8') as checkpoint:
        checkpoint.write(json.dumps(
            entry, ensure_ascii=False, allow_nan=False, separators=(',', ':'),
        ) + '\n')
        checkpoint.flush()
        os.fsync(checkpoint.fileno())


def _train_symbol(
    stock, config, methods, trial_settings, walk_forward_validation_days, device_index,
):
    symbol = str(stock['instrument'].iloc[0])
    method_results = {}
    for method in methods:
        metadata, forecasts = train_stock(
            stock, config, method, trial_settings, seed=42,
            walk_forward_validation_days=walk_forward_validation_days,
            device_index=device_index,
        )
        method_results[method] = (metadata, forecasts)
    return symbol, method_results


def run(args) -> dict:
    config = ForecastConfig(
        train_start=args.train_start, validation_start=args.validation_start,
        test_start=args.test_start, test_end=args.test_end,
    )
    config.validate()
    if isinstance(args.parallel_gpus, bool) or args.parallel_gpus < 1:
        raise DifferencingError('--parallel-gpus must be a positive integer')
    if isinstance(args.workers_per_gpu, bool) or args.workers_per_gpu < 1:
        raise DifferencingError('--workers-per-gpu must be a positive integer')
    parallel_mode = args.parallel_gpus > 1 or args.workers_per_gpu > 1
    if parallel_mode:
        import torch

        available_gpus = torch.cuda.device_count() if torch.cuda.is_available() else 0
        if args.parallel_gpus > available_gpus:
            raise DifferencingError(
                f'--parallel-gpus requested {args.parallel_gpus}, but only '
                f'{available_gpus} CUDA devices are available',
            )
    if args.output.exists():
        raise DifferencingError('Refusing to overwrite an existing experiment')
    prices, universe, provenance = load_fractional_database(
        args.database, config, seed=args.seed, universe_size=args.universe_size,
    )
    candidates = universe.members_between(config.test_start, config.test_end)
    models = {}
    checkpoint = _checkpoint_path(args.output)
    models, predictions, completed_symbols = _restore_checkpoint(
        checkpoint, _checkpoint_signature(args),
    )
    if not completed_symbols <= set(candidates):
        raise DifferencingError(
            'Checkpoint contains symbols outside the selected stock universe',
        )
    trial_settings = [LSTMTrial(hidden_size=size, epochs=args.epochs) for size in (16, 32)]
    print(
        f'Resuming {len(completed_symbols)}/{len(candidates)} stocks; '
        f'{len(predictions)} methods, '
        f'{args.parallel_gpus} GPU(s) x {args.workers_per_gpu} worker(s) per GPU',
        flush=True,
    )
    if not parallel_mode:
        for symbol in candidates:
            if symbol in completed_symbols:
                continue
            stock = prices[prices['instrument'] == symbol]
            trained_symbol, method_results = _train_symbol(
                stock, config, tuple(predictions), trial_settings,
                args.walk_forward_validation_days, None,
            )
            for method, (metadata, forecasts) in method_results.items():
                models[f'{trained_symbol}:{method}'] = metadata
                predictions[method].update(forecasts)
            _append_checkpoint(checkpoint, trained_symbol, method_results)
            completed_symbols.add(trained_symbol)
            print(
                f'Completed stock {len(completed_symbols)}/{len(candidates)}: '
                f'{trained_symbol}',
                flush=True,
            )
    else:
        with ExitStack() as stack:
            workers = [
                stack.enter_context(
                    ProcessPoolExecutor(max_workers=args.workers_per_gpu),
                )
                for _ in range(args.parallel_gpus)
            ]
            future_jobs = {}
            for index, symbol in enumerate(candidates):
                if symbol in completed_symbols:
                    continue
                gpu_index = index % args.parallel_gpus
                stock = prices[prices['instrument'] == symbol].copy()
                future = workers[gpu_index].submit(
                    _train_symbol, stock, config, tuple(predictions), trial_settings,
                    args.walk_forward_validation_days, gpu_index,
                )
                future_jobs[future] = (symbol, gpu_index)

            completed = 0
            for future in as_completed(future_jobs):
                expected_symbol, gpu_index = future_jobs[future]
                trained_symbol, method_results = future.result()
                if trained_symbol != expected_symbol:
                    raise DifferencingError(
                        f'Worker for {expected_symbol} returned {trained_symbol}',
                    )
                for method, (metadata, forecasts) in method_results.items():
                    models[f'{trained_symbol}:{method}'] = metadata
                    predictions[method].update(forecasts)
                _append_checkpoint(checkpoint, trained_symbol, method_results)
                completed_symbols.add(trained_symbol)
                completed += 1
                print(
                    f'Completed stock {len(completed_symbols)}/{len(candidates)}: {trained_symbol} '
                    f'(GPU {gpu_index})',
                    flush=True,
                )

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
            f"从stocks.db按固定随机种子抽取{args.universe_size}只具有完整历史的上海非ETF股票；"
            f"存在幸存者偏差，并非上证50。"
        ),
        'data_provenance': provenance,
        'inputs': {'database': provenance},
        'parameters': {
            'train_start': config.train_start.isoformat(),
            'validation_start': config.validation_start.isoformat(),
            'test_start': config.test_start.isoformat(),
            'test_end': config.test_end.isoformat(),
            'seed': args.seed,
            'model_seed': 42,
            'universe_size': args.universe_size,
            'parallel_gpus': args.parallel_gpus,
            'workers_per_gpu': args.workers_per_gpu,
            'walk_forward_validation_days': args.walk_forward_validation_days,
            'buy_cost': args.buy_cost,
            'sell_cost': args.sell_cost,
            'signal_threshold': args.signal_threshold,
            'initial_capital': args.capital,
        },
        'models': models,
        'forecasts': {
            method: [
                {'date': day.isoformat(), 'instrument': symbol, 'predicted_return': value}
                for (day, symbol), value in sorted(forecasts.items())
            ]
            for method, forecasts in predictions.items()
        },
        'backtests': runs,
        'deviations': [
            'A seeded sample from the database replaces historical SSE50 membership; the sample has survivorship bias.',
            'Database adjusted-close ratios are applied to OHLC prices.',
            'De Prado and first-difference branches only; no ARFIMA/ARTFIMA R estimator replication.',
            'ADF grid 0.05, truncation 0.001, AIC lag selection are disclosed implementation settings.',
            'Single-layer PyTorch LSTM; independent-stock GPU workers are used only when --parallel-gpus exceeds 1.',
            'Hidden16/32, daily walk-forward model/epoch selection on the preceding 60 labeled samples; every prediction is fit only on data before its target date.',
            'Daily equal allocation slots; no reallocation of inactive slots, 95% max exposure.',
            'Research costs cannot replace actual A-share commissions or execution rules.',
            'Only a research simulator; actual stock execution must be validated separately.',
        ],
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--database', type=Path, default=STOCKS_DATABASE_PATH,
        help='Read-only stocks.db path',
    )
    parser.add_argument('--output', type=Path, required=True,
                        help='Chinese JSON results, including saved forecasts; refuses overwrite')
    parser.add_argument('--seed', type=int, default=42,
                        help='Stock-sample seed; model initialization stays fixed at 42')
    parser.add_argument('--universe-size', type=int, default=30)
    parser.add_argument(
        '--walk-forward-validation-days', type=int, default=60,
        help='Use this many immediately preceding trading-day samples for daily model selection',
    )
    parser.add_argument('--train-start', type=date.fromisoformat, default=date(2023, 1, 1))
    parser.add_argument('--validation-start', type=date.fromisoformat, default=date(2024, 1, 1))
    parser.add_argument('--test-start', type=date.fromisoformat, default=date(2025, 1, 1))
    parser.add_argument('--test-end', type=date.fromisoformat, default=date(2026, 10, 14))
    parser.add_argument('--capital', type=float, default=100000)
    parser.add_argument('--epochs', type=int, default=30)
    parser.add_argument(
        '--parallel-gpus', type=int, default=1,
        help='Train independent stocks on this many GPUs (default: 1)',
    )
    parser.add_argument(
        '--workers-per-gpu', type=int, default=1,
        help='Concurrent stock-training processes per GPU (default: 1)',
    )
    parser.add_argument('--buy-cost', type=float, default=0.0005)
    parser.add_argument('--sell-cost', type=float, default=0.001)
    parser.add_argument('--signal-threshold', type=float, default=0.002)
    args = parser.parse_args()
    try:
        result = run(args)
        with args.output.open('x', encoding='utf-8') as output:
            json.dump(chinese_result(result), output, ensure_ascii=False, allow_nan=False, indent=2)
        _checkpoint_path(args.output).unlink()
    except (OSError, ValueError, ImportError) as exc:
        parser.exit(1, f'Research stopped: {exc}\n')
    print(f'Research result: {args.output}')


if __name__ == '__main__':
    main()
