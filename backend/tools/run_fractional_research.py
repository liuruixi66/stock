"""Run the database-backed Shanghai-stock LSTM research experiment."""

import argparse
from dataclasses import asdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import ExitStack
from datetime import date
import hashlib
import json
import logging
from logging.handlers import QueueHandler, QueueListener
import math
import multiprocessing
import os
from pathlib import Path
import sys
from time import strftime

from config.settings import STOCKS_DATABASE_PATH
from research.database_fractional import load_fractional_database
from research.fractional_forecast import (
    DifferencingError, ForecastConfig, simulate_long_only,
)
from research.fractional_lstm import (
    LSTMTrial, evaluate_return_predictions, train_stock,
)
from research.fractional_results import chinese_result
from market_data.price_basis import research_price_contract


CHECKPOINT_VERSION = 3
METHODS = ('de_prado', 'log_return')


def _configure_worker_logging(log_queue) -> None:
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(QueueHandler(log_queue))
    root_logger.setLevel(logging.INFO)


def _checkpoint_signature(args) -> str:
    database = args.database.expanduser().resolve()
    stat = database.stat()
    parameters = {
        'price_contract': research_price_contract(),
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
        'training_mode': args.training_mode,
        'patience': args.early_stopping_patience,
        'min_delta': args.min_delta,
        'search_signature': args.search_signature,
        'trial_settings': args.trial_settings,
        'model_directory': str(args.model_directory.resolve()),
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
                'price_contract': research_price_contract(),
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
                or header.get('signature') != signature
                or header.get('price_contract') != research_price_contract()):
            raise DifferencingError(
                f'Checkpoint version or experiment/price policy differs: {path}; '
                'preserve the old checkpoint and use a new output filename',
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
    patience=0, min_delta=1e-6, selection_metric='scaled_mse',
    checkpoint_directory=None,
):
    symbol = str(stock['instrument'].iloc[0])
    method_results = {}
    for method in methods:
        metadata, forecasts = train_stock(
            stock, config, method, trial_settings[method], seed=42,
            walk_forward_validation_days=walk_forward_validation_days,
            device_index=device_index,
            patience=patience, min_delta=min_delta, selection_metric=selection_metric,
            checkpoint_directory=checkpoint_directory,
        )
        method_results[method] = (metadata, forecasts)
    return symbol, method_results


def _model_evaluations(prices, predictions, backtests) -> dict:
    actual_returns = {}
    for symbol, rows in prices.groupby('instrument', sort=False):
        ordered = rows.sort_values('date')
        dates = ordered['date'].tolist()
        closes = ordered['close'].tolist()
        for index in range(len(dates) - 1):
            actual_returns[(dates[index], symbol)] = closes[index + 1] / closes[index] - 1

    machine_learning = {}
    for method, forecasts in predictions.items():
        missing_actuals = [key for key in forecasts if key not in actual_returns]
        if missing_actuals:
            raise DifferencingError(
                f'{method} forecasts lack matching actual returns: {missing_actuals[:5]}',
            )
        actual = [actual_returns[key] for key in forecasts]
        predicted = [forecasts[key] for key in forecasts]
        machine_learning[method] = {
            **evaluate_return_predictions(actual, predicted),
            'zero_return_baseline': evaluate_return_predictions(
                actual, [0.0] * len(actual),
            ),
        }

    benchmark_name = 'database_random_equal_slot'
    benchmark = backtests[benchmark_name]
    financial = {}
    financial_metrics = (
        'total_return', 'annualized_return', 'max_drawdown',
        'annualized_volatility', 'sharpe_zero_risk_free', 'costs', 'order_count',
    )
    for method in predictions:
        strategy = backtests[method]
        differences = {}
        for metric in (
            'total_return', 'annualized_return', 'max_drawdown',
            'annualized_volatility', 'sharpe_zero_risk_free',
        ):
            strategy_value = strategy[metric]
            benchmark_value = benchmark[metric]
            differences[f'{metric}_difference_vs_benchmark'] = (
                strategy_value - benchmark_value
                if strategy_value is not None and benchmark_value is not None else None
            )
        financial[method] = {
            **{metric: strategy[metric] for metric in financial_metrics},
            'benchmark': benchmark_name,
            'benchmark_metrics': {
                metric: benchmark[metric] for metric in financial_metrics
            },
            **differences,
        }

    return {
        'machine_learning': {
            'evaluation_period': 'test',
            'target': 'next_trading_day_adjusted_close_simple_return',
            'methods': machine_learning,
            'notes': [
                'Metrics pool all out-of-sample stock-day forecasts; the baseline predicts zero return.',
                'MAPE excludes exact-zero actual returns and is sensitive to small nonzero returns.',
                'Directional accuracy compares the signs of predicted and actual returns, including zero as a separate direction.',
            ],
        },
        'financial': {
            'methods': financial,
            'notes': [
                'Returns and risk metrics come from the research simulator and are compared with the database random equal-slot benchmark.',
                'These results do not model all real A-share execution constraints and are not live-trading performance.',
            ],
        },
    }


def run(args) -> dict:
    tuned = args.training_mode == 'tuned'
    args.train_start = args.train_start or (
        date(2006, 10, 16) if tuned else date(2023, 1, 1)
    )
    args.validation_start = args.validation_start or (
        date(2014, 10, 14) if tuned else date(2024, 1, 1)
    )
    args.epochs = args.epochs if args.epochs is not None else (120 if tuned else 30)
    if not tuned:
        args.early_stopping_patience = 0
    args.model_directory = args.model_directory or args.output.with_name(
        args.output.name + '.models',
    )
    config = ForecastConfig(
        train_start=args.train_start, validation_start=args.validation_start,
        test_start=args.test_start, test_end=args.test_end,
    )
    config.validate()
    logging.warning(
        'Research-only vendor adjusted snapshot; not certified qfq/hfq or '
        'point-in-time. Vendor OHLC is not verified nominal execution data.',
    )
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
    checkpoint = _checkpoint_path(args.output)
    if args.model_directory.exists() and not checkpoint.exists():
        raise DifferencingError(
            'Model directory already exists without matching stock progress; '
            'use a new output/model directory instead of overwriting saved weights',
        )
    search_report = None
    args.search_signature = None
    selection_metric = 'return_mae' if tuned else 'scaled_mse'
    if tuned:
        from research.fractional_tuning import SearchSettings, run_search

        if args.train_start > date(2006, 10, 16):
            raise DifferencingError(
                'Tuned mode requires training history from 2006-10-16; '
                'use --training-mode legacy for a shorter dataset',
            )
        args.search_directory = args.search_directory or args.output.with_name(
            args.output.name + '.search',
        )
        search_report = run_search(
            args.database, args.search_directory, SearchSettings(
                stock_count=args.search_stocks, total_trials=args.search_trials,
                max_epochs=args.epochs, patience=args.early_stopping_patience,
                min_delta=args.min_delta, seed=args.seed,
            ), test_start=args.test_start, resume=args.resume_search,
        )
        trial_settings = {
            method: [LSTMTrial(**search_report['methods'][method]['selected_trial'])]
            for method in METHODS
        }
        args.search_signature = search_report['signature']
        for method in METHODS:
            if not search_report['methods'][method]['qualified_vs_zero_baseline']:
                logging.warning(
                    '%s search winner does NOT beat zero-return MAE; research only',
                    method,
                )
    else:
        trial_settings = {
            method: [LSTMTrial(hidden_size=size, epochs=args.epochs) for size in (16, 32)]
            for method in METHODS
        }
    args.trial_settings = {
        method: [asdict(trial) for trial in trials]
        for method, trials in trial_settings.items()
    }
    logging.info('Effective training mode=%s trials=%s patience=%d metric=%s',
                 args.training_mode, args.trial_settings, args.early_stopping_patience,
                 selection_metric)
    prices, universe, provenance = load_fractional_database(
        args.database, config, seed=args.seed, universe_size=args.universe_size,
    )
    candidates = universe.members_between(config.test_start, config.test_end)
    models = {}
    models, predictions, completed_symbols = _restore_checkpoint(
        checkpoint, _checkpoint_signature(args),
    )
    if not completed_symbols <= set(candidates):
        raise DifferencingError(
            'Checkpoint contains symbols outside the selected stock universe',
        )
    logging.info(
        f'Resuming {len(completed_symbols)}/{len(candidates)} stocks; '
        f'{len(predictions)} methods, '
        f'{args.parallel_gpus} GPU(s) x {args.workers_per_gpu} worker(s) per GPU',
    )
    if not parallel_mode:
        for symbol in candidates:
            if symbol in completed_symbols:
                continue
            stock = prices[prices['instrument'] == symbol]
            trained_symbol, method_results = _train_symbol(
                stock, config, tuple(predictions), trial_settings,
                args.walk_forward_validation_days, None,
                args.early_stopping_patience, args.min_delta, selection_metric,
                args.model_directory,
            )
            for method, (metadata, forecasts) in method_results.items():
                models[f'{trained_symbol}:{method}'] = metadata
                predictions[method].update(forecasts)
            _append_checkpoint(checkpoint, trained_symbol, method_results)
            completed_symbols.add(trained_symbol)
            logging.info(
                f'Completed stock {len(completed_symbols)}/{len(candidates)}: '
                f'{trained_symbol}',
            )
    else:
        with ExitStack() as stack:
            workers = [
                stack.enter_context(
                    ProcessPoolExecutor(
                        max_workers=args.workers_per_gpu,
                        initializer=_configure_worker_logging,
                        initargs=(args.log_queue,),
                    ),
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
                    args.early_stopping_patience, args.min_delta, selection_metric,
                    args.model_directory,
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
                logging.info(
                    f'Completed stock {len(completed_symbols)}/{len(candidates)}: {trained_symbol} '
                    f'(GPU {gpu_index})',
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
    evaluations = _model_evaluations(prices, predictions, runs)
    return {
        'price_contract': research_price_contract(),
        'paper': 'https://arxiv.org/abs/2505.19243',
        'status': 'method_migration_not_exact_replication',
        'universe': (
            f"从stocks.db按固定随机种子抽取{args.universe_size}只具有完整历史的上海非ETF股票；"
            f"存在幸存者偏差，并非上证50。"
        ),
        'data_provenance': provenance,
        'inputs': {'database': provenance},
        'hyperparameter_search': {
            'report_path': str(args.search_directory.resolve() / 'report.json'),
            'signature': args.search_signature,
            'qualification': {
                method: search_report['methods'][method]['qualified_vs_zero_baseline']
                for method in METHODS
            },
        } if search_report is not None else None,
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
            'training_mode': args.training_mode, 'trial_settings': args.trial_settings,
            'early_stopping_patience': args.early_stopping_patience,
            'min_delta': args.min_delta, 'selection_metric': selection_metric,
            'model_directory': str(args.model_directory.resolve()),
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
        'evaluations': evaluations,
        'deviations': [
            'A seeded sample from the database replaces historical SSE50 membership; the sample has survivorship bias.',
            'Database adjusted-close ratios are applied to OHLC prices.',
            'De Prado and first-difference branches only; no ARFIMA/ARTFIMA R estimator replication.',
            'ADF grid 0.05, truncation 0.001, AIC lag selection are disclosed implementation settings.',
            'PyTorch LSTM; effective layer/width/search settings are recorded in parameters.',
            'Daily walk-forward epoch selection uses only preceding labeled samples; search configuration is frozen before test forecasts.',
            'Daily equal allocation slots; no reallocation of inactive slots, 95% max exposure.',
            'Research costs cannot replace actual A-share commissions or execution rules.',
            'Only a research simulator; actual stock execution must be validated separately.',
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--database', type=Path, default=STOCKS_DATABASE_PATH,
        help='Read-only stocks.db path',
    )
    parser.add_argument('--output', type=Path, required=True,
                        help='Chinese JSON results, including saved forecasts; refuses overwrite')
    parser.add_argument('--seed', type=int, default=42,
                        help='Stock-sample/search seed; walk-forward initialization stays 42')
    parser.add_argument('--universe-size', type=int, default=30)
    parser.add_argument(
        '--walk-forward-validation-days', type=int, default=60,
        help='Use this many immediately preceding trading-day samples for daily model selection',
    )
    parser.add_argument('--train-start', type=date.fromisoformat)
    parser.add_argument('--validation-start', type=date.fromisoformat)
    parser.add_argument('--test-start', type=date.fromisoformat, default=date(2025, 1, 1))
    parser.add_argument('--test-end', type=date.fromisoformat, default=date(2026, 10, 14))
    parser.add_argument('--capital', type=float, default=100000)
    parser.add_argument('--epochs', type=int, help='Tuned maximum defaults to 120; legacy to 30')
    parser.add_argument('--training-mode', choices=('tuned', 'legacy'), default='tuned')
    parser.add_argument('--early-stopping-patience', type=int, default=15)
    parser.add_argument('--min-delta', type=float, default=1e-6)
    parser.add_argument('--search-directory', type=Path)
    parser.add_argument('--resume-search', action='store_true')
    parser.add_argument('--search-trials', type=int, default=20, help='Total across both methods')
    parser.add_argument('--search-stocks', type=int, default=6)
    parser.add_argument('--model-directory', type=Path)
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
    parser.add_argument(
        '--log-directory', type=Path,
        default=Path(__file__).resolve().parents[1] / 'log',
        help='Directory for timestamped training logs',
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.log_directory.mkdir(parents=True, exist_ok=True)
    log_path = args.log_directory / (
        f'fractional-research-seed-{args.seed}-{strftime("%Y%m%d-%H%M%S")}.log'
    )
    log_queue = multiprocessing.get_context('spawn').Queue()
    args.log_queue = log_queue
    log_format = logging.Formatter('%(asctime)s %(levelname)s %(processName)s %(message)s')
    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    console_handler.setFormatter(log_format)
    file_handler.setFormatter(log_format)
    listener = QueueListener(
        log_queue, console_handler, file_handler, respect_handler_level=True,
    )
    listener.start()
    _configure_worker_logging(log_queue)
    logging.info('Training log: %s', log_path)
    try:
        result = run(args)
        with args.output.open('x', encoding='utf-8') as output:
            json.dump(chinese_result(result), output, ensure_ascii=False, allow_nan=False, indent=2)
        _checkpoint_path(args.output).unlink()
    except (OSError, ValueError, ImportError) as exc:
        logging.exception('Research stopped: %s', exc)
        parser.exit(1, f'Research stopped: {exc}\nLog: {log_path}\n')
    else:
        logging.info('Research result: %s', args.output)
    finally:
        listener.stop()
        log_queue.close()


if __name__ == '__main__':
    main()
