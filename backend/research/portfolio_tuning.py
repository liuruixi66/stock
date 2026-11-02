"""Portfolio-level shared-LSTM validation search on the frozen Tushare universe."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
import json
import logging
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import pandas as pd
import torch

from market_data.industry_universe import verify_industry_universe
from market_data.portfolio_history import (
    load_portfolio_history, portfolio_price_contract,
)
from research.fractional_forecast import (
    DifferencingError, ForecastConfig, estimate_order, fractional_weights,
)
from research.fractional_lstm import training_device
from research.fractional_tuning import atomic_json
from research.portfolio_lstm import (
    FEATURE_NAMES, PortfolioModelConfig, SharedPortfolioLSTM,
    build_feature_frame, fit_feature_scaler, select_positions,
    save_model_bundle, train_shared_model, unwrap_shared_model,
    wrap_model_for_training,
)


logger = logging.getLogger(__name__)
SEARCH_VERSION = 1
SEARCH_METHODS = ('de_prado', 'log_return')
UNEXPLAINED_GAP_EXCLUSIONS = {
    '000156.SZ', '000506.SZ', '000592.SZ', '000620.SZ',
    '000657.SZ', '000681.SZ', '600633.SH', '600732.SH',
}


@dataclass(frozen=True)
class PortfolioSearchSettings:
    train_start: date = date(2006, 10, 16)
    fold_years: tuple[int, ...] = (2012, 2013, 2014)
    total_trials: int = 20
    max_epochs: int = 120
    patience: int = 15
    seed: int = 42
    test_start: date = date(2016, 10, 14)
    initial_capital: float = 100000.0
    sequence_length: int = 20
    positions: int = 30
    exposure: float = 0.95
    buy_cost: float = 0.0005
    sell_cost: float = 0.001
    signal_threshold: float = 0.002
    max_drawdown: float = 0.20

    def validate(self) -> None:
        if self.total_trials != 20:
            raise ValueError('The approved portfolio search uses exactly 20 trials')
        if self.fold_years != (2012, 2013, 2014):
            raise ValueError('The approved validation folds are 2012, 2013 and 2014')
        if (self.max_epochs != 120 or self.patience != 15 or self.seed != 42
                or self.sequence_length != 20 or self.positions != 30):
            raise ValueError('Search settings differ from the approved experiment protocol')
        if (not self.train_start < date(self.fold_years[0], 1, 1)
                or self.test_start <= date(self.fold_years[-1] + 1, 1, 1)
                or self.initial_capital != 100000
                or self.exposure != .95 or self.buy_cost != .0005
                or self.sell_cost != .001 or self.signal_threshold != .002
                or self.max_drawdown != .20):
            raise ValueError('Portfolio search settings differ from the approved protocol')


@dataclass
class PortfolioPanel:
    dates: list[date]
    symbols: list[str]
    features: np.ndarray
    feature_valid: np.ndarray
    opens: np.ndarray
    closes: np.ndarray
    volumes: np.ndarray
    suspended: np.ndarray
    returns: np.ndarray
    eligible: np.ndarray
    weights: dict[str, list[float]]
    excluded_symbols: dict[str, str]
    scaler: dict
    sequence_length: int

    def sequence_batch(self, indices: np.ndarray) -> np.ndarray:
        return np.stack([
            self.features[index - self.sequence_length + 1:index + 1].transpose(1, 0, 2)
            for index in indices
        ]).astype(np.float32, copy=False)


def _fit_symbol_weights(
    prices: pd.DataFrame,
    symbols: Sequence[str],
    method: str,
    train_start: date,
    validation_start: date,
    validation_end: date,
) -> tuple[dict[str, list[float]], dict[str, str]]:
    weights, excluded = {}, {}
    if method not in SEARCH_METHODS:
        raise ValueError(f'Unsupported portfolio differencing method: {method}')
    fixed = fractional_weights(1.0)
    for symbol in symbols:
        stock = prices.loc[
            (prices['instrument'] == symbol) & (prices['date'] >= train_start)
            & (prices['date'] < validation_start)
        ].sort_values('date')
        if method == 'log_return':
            weights[symbol] = fixed.tolist()
            continue
        if len(stock) < 252:
            excluded[symbol] = 'insufficient_training_history_for_adf'
            continue
        config = ForecastConfig(
            train_start=train_start, validation_start=validation_start - timedelta(days=1),
            test_start=validation_start, test_end=validation_end,
            sequence_length=20,
        )
        try:
            details = estimate_order(np.log(stock['close'].to_numpy()), config)
        except DifferencingError as exc:
            excluded[symbol] = f'adf_order_unavailable: {exc}'
            continue
        weights[symbol] = fractional_weights(details['order']).tolist()
    if not weights:
        raise ValueError(f'No symbol has valid differencing weights for {method} {validation_start}')
    return weights, excluded


def build_portfolio_panel(
    prices: pd.DataFrame,
    sessions: Sequence[date],
    suspended_sessions: Mapping[str, set[str]],
    symbols: Sequence[str],
    weights: Mapping[str, Sequence[float]],
    *,
    train_start: date,
    validation_start: date,
    sequence_length: int = 20,
) -> PortfolioPanel:
    if prices.empty or not symbols or not sessions:
        raise ValueError('Prices, calendar and frozen symbols must be nonempty')
    if set(weights) - set(symbols):
        raise ValueError('Differencing weights contain symbols outside the frozen universe')
    dates = [pd.Timestamp(day).date() for day in sessions]
    if dates != sorted(set(dates)):
        raise ValueError('Trading sessions must be unique and sorted')
    symbol_index = {symbol: index for index, symbol in enumerate(symbols)}
    date_index = {day: index for index, day in enumerate(dates)}
    stock_count, day_count, feature_count = len(symbols), len(dates), len(FEATURE_NAMES)
    features = np.zeros((day_count, stock_count, feature_count), dtype=np.float32)
    feature_valid = np.zeros((day_count, stock_count), dtype=bool)
    opens = np.full((day_count, stock_count), np.nan, dtype=np.float64)
    closes = np.full_like(opens, np.nan)
    volumes = np.zeros((day_count, stock_count), dtype=np.float32)
    suspended = np.zeros((day_count, stock_count), dtype=bool)
    excluded = {symbol: 'differencing_order_unavailable' for symbol in set(symbols) - set(weights)}
    grouped = {symbol: stock for symbol, stock in prices.groupby('instrument', sort=False)}

    for symbol in symbols:
        stock_index = symbol_index[symbol]
        stock = grouped.get(symbol)
        if stock is None:
            excluded[symbol] = 'no_price_rows'
            continue
        for row in stock.itertuples(index=False):
            day = pd.Timestamp(row.date).date()
            if day not in date_index:
                raise ValueError(f'Price date outside market calendar: {symbol} {day}')
            index = date_index[day]
            opens[index, stock_index] = float(row.open)
            closes[index, stock_index] = float(row.close)
            volumes[index, stock_index] = float(row.volume)
            suspended[index, stock_index] = bool(row.suspended)
        for raw_day in suspended_sessions.get(symbol, set()):
            day = pd.to_datetime(raw_day, format='%Y%m%d').date()
            if day in date_index:
                suspended[date_index[day], stock_index] = True
        if symbol not in weights:
            continue
        transformed = build_feature_frame(stock, dates, weights[symbol])
        for row in transformed.itertuples(index=False):
            index = date_index[pd.Timestamp(row.date).date()]
            values = np.asarray([getattr(row, name) for name in FEATURE_NAMES], dtype=np.float64)
            if np.isfinite(values).all():
                features[index, stock_index] = values
                feature_valid[index, stock_index] = True

    returns = np.zeros((day_count - 1, stock_count), dtype=np.float32)
    eligible = np.zeros((day_count - 1, stock_count), dtype=bool)
    for index in range(day_count - 1):
        both_quotes = np.isfinite(closes[index]) & np.isfinite(closes[index + 1])
        valid = (
            both_quotes & (volumes[index] > 0) & (volumes[index + 1] > 0)
            & ~suspended[index] & ~suspended[index + 1]
        )
        returns[index, valid] = (
            closes[index + 1, valid] / closes[index, valid] - 1
        ).astype(np.float32)
        eligible[index] = valid

    train_indices = [
        index for index in range(day_count - 1)
        if train_start <= dates[index] < validation_start
        and dates[index + 1] < validation_start
    ]
    train_mask = np.zeros_like(feature_valid)
    if train_indices:
        train_mask[train_indices] = feature_valid[train_indices]
    training_feature_rows = features[train_mask]
    if not len(training_feature_rows):
        raise ValueError('No valid training features for shared scaler')
    scaler = fit_feature_scaler(training_feature_rows[:, None, :])
    mean = np.asarray(scaler['mean'], dtype=np.float32)
    scale = np.asarray(scaler['scale'], dtype=np.float32)
    features[feature_valid] = (features[feature_valid] - mean) / scale
    features[~feature_valid] = 0.0

    window_valid = np.zeros_like(feature_valid)
    for index in range(sequence_length - 1, day_count - 1):
        window_valid[index] = feature_valid[
            index - sequence_length + 1:index + 1
        ].all(axis=0)
    eligible &= window_valid[:-1]
    return PortfolioPanel(
        dates, list(symbols), features, feature_valid, opens, closes, volumes,
        suspended, returns, eligible, dict(weights), excluded, scaler, sequence_length,
    )


def _training_batches(
    panel: PortfolioPanel,
    validation_start: date,
    batch_size: int,
) -> list[dict[str, torch.Tensor]]:
    date_indices = np.asarray([
        index for index in range(panel.sequence_length - 1, len(panel.dates) - 1)
        if panel.dates[index] >= panel.dates[panel.sequence_length - 1]
        and panel.dates[index] < validation_start
        and panel.eligible[index].any()
    ], dtype=np.int64)
    batches = []
    for start in range(0, len(date_indices), batch_size):
        selected = date_indices[start:start + batch_size]
        if not len(selected):
            continue
        batches.append({
            'sequences': torch.from_numpy(panel.sequence_batch(selected)),
            'returns': torch.from_numpy(panel.returns[selected]),
            'eligible': torch.from_numpy(panel.eligible[selected]),
            'previous': torch.zeros_like(torch.from_numpy(panel.returns[selected])),
        })
    if not batches:
        raise ValueError('No valid portfolio training batches before validation')
    return batches


def simulate_portfolio(
    panel: PortfolioPanel,
    scores: np.ndarray,
    signal_indices: Sequence[int],
    config: PortfolioModelConfig,
    initial_capital: float = 100000.0,
) -> dict:
    """Exact daily target/next-open accounting for the research price protocol."""
    if scores.shape != (len(panel.dates), len(panel.symbols)):
        raise ValueError('Score panel shape does not match dates and symbols')
    cash, units, last_prices = float(initial_capital), {}, {}
    pending = None
    curve, trades = [], []
    fees = 0.0
    peak = initial_capital
    maximum_drawdown = 0.0
    indices = list(signal_indices)
    if not indices:
        raise ValueError('Validation needs at least one signal date')
    for position, day_index in enumerate(indices):
        day = panel.dates[day_index]
        quote_rows = {
            symbol: (panel.opens[day_index, index], panel.closes[day_index, index],
                     panel.volumes[day_index, index], panel.suspended[day_index, index])
            for index, symbol in enumerate(panel.symbols)
            if np.isfinite(panel.closes[day_index, index])
        }
        for symbol, (_, close, volume, _) in quote_rows.items():
            if volume > 0:
                last_prices[symbol] = float(close)

        if pending is not None:
            origin, targets = pending
            equity_open = cash
            for symbol, quantity in units.items():
                row = quote_rows.get(symbol)
                if row and row[2] > 0 and not row[3]:
                    mark = float(row[0])
                else:
                    mark = last_prices.get(symbol)
                if mark is None:
                    raise ValueError(f'No valuation price for held position {symbol} on {day}')
                equity_open += quantity * mark
            for symbol in sorted(units):
                row = quote_rows.get(symbol)
                if not row or row[2] <= 0 or row[3]:
                    continue
                open_price = float(row[0])
                target_value = targets.get(symbol, 0.0) * equity_open
                reduction = max(0.0, units[symbol] * open_price - target_value)
                if reduction > 1e-8:
                    units[symbol] -= reduction / open_price
                    cost = reduction * config.sell_cost
                    cash += reduction - cost
                    fees += cost
                    trades.append({'signal_date': origin.isoformat(), 'date': day.isoformat(),
                                   'instrument': symbol, 'side': 'SELL',
                                   'value': reduction, 'cost': cost})
            units = {symbol: quantity for symbol, quantity in units.items()
                     if quantity > 1e-10}
            for symbol, weight in sorted(targets.items()):
                row = quote_rows.get(symbol)
                if weight <= 0 or not row or row[2] <= 0 or row[3]:
                    continue
                open_price = float(row[0])
                current_value = units.get(symbol, 0.0) * open_price
                increase = min(
                    max(0.0, weight * equity_open - current_value),
                    max(0.0, cash) / (1 + config.buy_cost),
                )
                if increase > 1e-8:
                    units[symbol] = units.get(symbol, 0.0) + increase / open_price
                    cost = increase * config.buy_cost
                    cash -= increase + cost
                    fees += cost
                    trades.append({'signal_date': origin.isoformat(), 'date': day.isoformat(),
                                   'instrument': symbol, 'side': 'BUY',
                                   'value': increase, 'cost': cost})

        equity = cash
        for symbol, quantity in units.items():
            row = quote_rows.get(symbol)
            mark = (float(row[1]) if row and row[2] > 0
                    else last_prices.get(symbol))
            if mark is None:
                raise ValueError(f'No closing valuation price for held position {symbol} on {day}')
            equity += quantity * mark
        if not math_isfinite_positive(equity):
            raise ValueError(f'Invalid portfolio equity on {day}: {equity}')
        peak = max(peak, equity)
        maximum_drawdown = max(maximum_drawdown, 1 - equity / peak)
        curve.append({'date': day.isoformat(), 'equity': equity,
                      'drawdown': 1 - equity / peak})

        if position == len(indices) - 1:
            break
        previous_weights = {
            symbol: quantity * last_prices[symbol] / equity
            for symbol, quantity in units.items() if symbol in last_prices
        }
        day_scores, eligible_symbols = {}, set()
        for index, symbol in enumerate(panel.symbols):
            if panel.eligible[day_index, index] and np.isfinite(scores[day_index, index]):
                day_scores[symbol] = float(scores[day_index, index])
                eligible_symbols.add(symbol)
        for symbol in units:
            if symbol not in eligible_symbols:
                day_scores[symbol] = max(day_scores.values(), default=0.0) + 1.0
                eligible_symbols.add(symbol)
        targets = select_positions(
            day_scores, previous=previous_weights, eligible=eligible_symbols, config=config,
        )
        pending = (day, targets)

    final_equity = curve[-1]['equity']
    return {
        'initial_capital': initial_capital, 'final_equity': final_equity,
        'portfolio_return': final_equity / initial_capital - 1,
        'max_drawdown': maximum_drawdown, 'fees': fees,
        'trade_count': len(trades), 'curve': curve, 'trades': trades,
    }


def math_isfinite_positive(value: float) -> bool:
    return bool(np.isfinite(value) and value > 0)


def score_panel(
    model: SharedPortfolioLSTM,
    panel: PortfolioPanel,
    indices: Sequence[int],
    batch_size: int,
) -> np.ndarray:
    parameter = next(model.parameters())
    output = np.full((len(panel.dates), len(panel.symbols)), np.nan, dtype=np.float32)
    model.eval()
    with torch.no_grad():
        for offset in range(0, len(indices), batch_size):
            selected = np.asarray(indices[offset:offset + batch_size], dtype=np.int64)
            if not len(selected):
                continue
            sequences = torch.from_numpy(panel.sequence_batch(selected)).to(
                device=parameter.device, dtype=parameter.dtype,
            )
            flat = sequences.reshape(
                -1, panel.sequence_length, len(FEATURE_NAMES),
            )
            values = model(flat).reshape(len(selected), len(panel.symbols))
            output[selected] = values.detach().cpu().numpy()
    if not np.isfinite(output[np.asarray(indices, dtype=np.int64)]).all():
        raise ValueError('Validation inference produced non-finite scores')
    return output


def _trial_config(trial, settings: PortfolioSearchSettings) -> PortfolioModelConfig:
    layers = trial.suggest_categorical('num_layers', [1, 2])
    return PortfolioModelConfig(
        hidden_size=trial.suggest_categorical('hidden_size', [16, 32, 64]),
        num_layers=layers,
        dropout=trial.suggest_categorical('dropout', [0.0, 0.1, 0.2]) if layers > 1 else 0.0,
        batch_size=trial.suggest_categorical('batch_size', [32, 64, 128]),
        learning_rate=trial.suggest_float('learning_rate', 0.0003, 0.003, log=True),
        sequence_length=settings.sequence_length,
        maximum_positions=settings.positions,
        exposure=settings.exposure,
        buy_cost=settings.buy_cost,
        sell_cost=settings.sell_cost,
        signal_threshold=settings.signal_threshold,
        max_drawdown_limit=settings.max_drawdown,
        max_epochs=settings.max_epochs,
        patience=settings.patience,
        seed=settings.seed,
    )


def _prepare_folds(
    prices: pd.DataFrame,
    sessions: Sequence[date],
    suspended_sessions: Mapping[str, set[str]],
    symbols: Sequence[str],
    settings: PortfolioSearchSettings,
) -> dict[str, dict[int, PortfolioPanel]]:
    folds = {method: {} for method in SEARCH_METHODS}
    for method in SEARCH_METHODS:
        for year in settings.fold_years:
            validation_start = date(year, 1, 1)
            validation_end = date(year, 12, 31)
            weights, excluded = _fit_symbol_weights(
                prices, symbols, method, settings.train_start,
                validation_start, validation_end,
            )
            panel = build_portfolio_panel(
                prices, sessions, suspended_sessions, symbols, weights,
                train_start=settings.train_start, validation_start=validation_start,
                sequence_length=settings.sequence_length,
            )
            panel.excluded_symbols.update(excluded)
            folds[method][year] = panel
            logger.info(
                '%s %d panel prepared: symbols=%d usable=%d excluded=%d',
                method, year, len(symbols), len(weights), len(panel.excluded_symbols),
            )
    return folds


def _run_trial(
    trial,
    method: str,
    folds: Mapping[int, PortfolioPanel],
    settings: PortfolioSearchSettings,
    device: torch.device,
    checkpoint_root: Path,
    universe_signature: str,
) -> float:
    import torch.nn as nn

    config = _trial_config(trial, settings)
    fold_results = {}
    for year in settings.fold_years:
        panel = folds[year]
        validation_start = date(year, 1, 1)
        validation_indices = [
            index for index, day in enumerate(panel.dates[:-1])
            if validation_start <= day <= date(year, 12, 31)
            and index >= panel.sequence_length - 1
        ]
        if not validation_indices:
            trial.set_user_attr('failure', f'no_validation_dates_{year}')
            return -1e6
        batches = _training_batches(panel, validation_start, config.batch_size)
        base_model = SharedPortfolioLSTM(len(FEATURE_NAMES), config).to(device)
        model = wrap_model_for_training(base_model, device)

        def evaluate(candidate, epoch):
            scores = score_panel(candidate, panel, validation_indices, config.batch_size)
            metrics = simulate_portfolio(
                panel, scores, validation_indices, config, settings.initial_capital,
            )
            trial.report(
                float(np.mean([item['equity'] for item in metrics['curve']])),
                step=(year - settings.fold_years[0]) * settings.max_epochs + epoch,
            )
            return {
                'portfolio_return': metrics['portfolio_return'],
                'max_drawdown_by_year': {str(year): metrics['max_drawdown']},
            }

        result = train_shared_model(
            model, batches, config, evaluate, validation_years=[str(year)],
        )
        if not result['selected']:
            trial.set_user_attr(f'fold_{year}', {
                'passed': False, 'epochs': result['epochs_completed'],
                'minimum_training_loss': result['minimum_training_loss'],
            })
            trial.set_user_attr('failure', f'no_drawdown_qualified_epoch_{year}')
            return -1e6
        scores = score_panel(model, panel, validation_indices, config.batch_size)
        metrics = simulate_portfolio(
            panel, scores, validation_indices, config, settings.initial_capital,
        )
        checkpoint = (
            checkpoint_root / method / f'trial-{trial.number:03d}' / f'fold-{year}'
        )
        save_model_bundle(
            checkpoint, unwrap_shared_model(model), config,
            sorted(panel.weights), panel.weights,
            panel.scaler, universe_signature,
            {
                'run_id': checkpoint_root.parent.parent.name,
                'method': method, 'trial': trial.number,
                'epoch': result['best_epoch'],
                'training_status': 'validation_selected_fold',
                'selection_metric': 'validation_portfolio_return_subject_to_drawdown',
                'validation': {
                    'passed': metrics['max_drawdown'] <= settings.max_drawdown,
                    'max_drawdown_limit': settings.max_drawdown,
                    'max_drawdown_by_year': {str(year): metrics['max_drawdown']},
                    'portfolio_return': metrics['portfolio_return'],
                },
            },
        )
        fold_results[str(year)] = metrics
        trial.set_user_attr(f'fold_{year}', {
            'passed': metrics['max_drawdown'] <= settings.max_drawdown,
            'return': metrics['portfolio_return'],
            'max_drawdown': metrics['max_drawdown'],
            'fees': metrics['fees'],
            'trade_count': metrics['trade_count'],
            'selected_epoch': result['history'][-1]['epoch'],
            'checkpoint_epoch': result['best_epoch'],
            'checkpoint': str(checkpoint),
        })
        if metrics['max_drawdown'] > settings.max_drawdown:
            trial.set_user_attr('failure', f'drawdown_gate_failed_{year}')
            return -1e6
    objective = float(np.mean([
        fold_results[str(year)]['portfolio_return'] for year in settings.fold_years
    ]))
    if not np.isfinite(objective):
        raise ValueError('Non-finite portfolio validation objective')
    trial.set_user_attr('qualified', True)
    trial.set_user_attr('folds', {
        year: {
            'return': fold_results[str(year)]['portfolio_return'],
            'max_drawdown': fold_results[str(year)]['max_drawdown'],
            'fees': fold_results[str(year)]['fees'],
        }
        for year in settings.fold_years
    })
    return objective


def run_portfolio_search(
    database: Path,
    universe_path: Path,
    directory: Path,
    settings: PortfolioSearchSettings | None = None,
) -> dict:
    import optuna

    settings = settings or PortfolioSearchSettings()
    settings.validate()
    database, universe_path, directory = (
        Path(database).resolve(), Path(universe_path).resolve(), Path(directory).resolve(),
    )
    if directory.exists():
        raise ValueError(f'Portfolio search directory already exists: {directory}')
    with universe_path.open('r', encoding='utf-8') as stream:
        universe = json.load(stream)
    verify_industry_universe(universe)
    if UNEXPLAINED_GAP_EXCLUSIONS & set(universe['selected_instruments']):
        raise ValueError('Frozen universe still contains an audited unexplained-gap instrument')
    if (len(universe['selected_instruments']) != 546
            or universe.get('exclusion_policy') !=
            'explicit_user_exclusions_without_industry_backfill'
            or set(item['instrument'] for item in universe['excluded_by_user'])
            != UNEXPLAINED_GAP_EXCLUSIONS):
        raise ValueError('Frozen universe does not match the user-approved 8-stock exclusion')
    directory.mkdir(parents=True)
    history_start = settings.train_start
    history_end = date(2026, 10, 30)
    prices, sessions, suspended_sessions, provenance = load_portfolio_history(
        database, universe, history_start, history_end,
    )
    if provenance['universe_signature'] != universe['signature']:
        raise ValueError('Loaded prices do not match the frozen universe signature')
    panels = _prepare_folds(
        prices, sessions, suspended_sessions, universe['selected_instruments'], settings,
    )
    signature_payload = {
        'search_version': SEARCH_VERSION,
        'settings': {key: value.isoformat() if isinstance(value, date) else value
                     for key, value in asdict(settings).items()},
        'universe_signature': universe['signature'],
        'prices_sha256': provenance['prices_sha256'],
        'calendar_sha256': provenance['calendar_sha256'],
        'price_contract': portfolio_price_contract(),
        'methods': list(SEARCH_METHODS),
    }
    manifest_path = directory / 'manifest.json'
    atomic_json(manifest_path, signature_payload)
    storage_path = directory / 'study.sqlite3'
    storage = optuna.storages.RDBStorage(
        url='sqlite:///' + storage_path.as_posix(),
        engine_kwargs={'connect_args': {'timeout': 60}},
    )
    report = {
        **signature_payload,
        'data_provenance': provenance,
        'methods': {},
        'live_trading_eligible': False,
        'training_started': True,
        'model_bundles_created': False,
        'limitations': [
            'Current industry snapshot lookback has survivorship and lookahead bias.',
            'Historical ST status is unknown; this experiment is not live eligible.',
            'The 2016-2026 interval has been viewed before and is historical re-evaluation.',
            'Training loss is a smooth portfolio proxy; validation uses exact daily discrete accounting.',
        ],
    }
    try:
        device = training_device()
        if device.type == 'cuda' and torch.cuda.device_count() > 1:
            logger.info(
                'Shared portfolio models use DataParallel GPUs: %s',
                [torch.cuda.get_device_name(index)
                 for index in range(torch.cuda.device_count())],
            )
        else:
            logger.info('Shared portfolio models use training device: %s', device)
        trial_count_per_method = settings.total_trials // len(SEARCH_METHODS)
        for method in SEARCH_METHODS:
            study = optuna.create_study(
                study_name=method, storage=storage, direction='maximize',
                sampler=optuna.samplers.TPESampler(seed=settings.seed, n_startup_trials=4),
                load_if_exists=False,
            )
            study.optimize(
                lambda trial: _run_trial(
                    trial, method, panels[method], settings, device,
                    directory / 'checkpoints', universe['signature'],
                ),
                n_trials=trial_count_per_method,
                gc_after_trial=True,
                show_progress_bar=False,
            )
            qualified = [
                trial for trial in study.trials
                if trial.user_attrs.get('qualified') is True
                and trial.value is not None and np.isfinite(trial.value)
            ]
            method_report = {
                'trial_count': len(study.trials),
                'qualified_trial_count': len(qualified),
                'trials': [{
                    'number': item.number, 'value': item.value,
                    'parameters': item.params, 'diagnostics': item.user_attrs,
                    'state': item.state.name,
                } for item in study.trials],
            }
            if qualified:
                winner = max(qualified, key=lambda item: (item.value, -item.number))
                method_report['winner'] = {
                    'trial': winner.number, 'validation_mean_return': winner.value,
                    'parameters': winner.params, 'diagnostics': winner.user_attrs,
                }
            else:
                method_report['winner'] = None
            report['methods'][method] = method_report
            atomic_json(directory / 'report.json', report)
        finalists = [
            (method, result['winner'])
            for method, result in report['methods'].items() if result['winner'] is not None
        ]
        if finalists:
            method, winner = max(finalists, key=lambda row: row[1]['validation_mean_return'])
            report['selected_method'] = method
            report['selected_trial'] = winner['trial']
            report['selected_parameters'] = winner['parameters']
            report['selected_validation'] = winner['diagnostics']['folds']
            report['search_qualified'] = True
        else:
            report['selected_method'] = None
            report['search_qualified'] = False
            report['failure'] = 'No trial passed every validation-year drawdown gate.'
        atomic_json(directory / 'report.json', report)
    finally:
        storage.remove_session()
        storage.engine.dispose()
    return report
