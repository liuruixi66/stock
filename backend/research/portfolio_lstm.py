"""Shared fractional-difference LSTM for portfolio-level research signals.

The module contains no broker integration. Its differentiable objective is a
training surrogate; portfolio selection and drawdown qualification must be
measured separately with the project's execution simulator.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import tempfile
from typing import Callable, Mapping, Sequence

import numpy as np
import pandas as pd
import torch
from torch import Tensor, nn

from research.fractional_forecast import fractional_difference


MODEL_BUNDLE_VERSION = 1
PRICE_PROTOCOL = 'tushare-factor-portfolio-research-v1'
FEATURE_NAMES = (
    'fractional_log_close',
    'log_return',
    'intraday_log_range',
    'overnight_log_gap',
    'log_volume_change',
)


@dataclass(frozen=True)
class PortfolioModelConfig:
    hidden_size: int = 32
    num_layers: int = 1
    dropout: float = 0.0
    batch_size: int = 64
    learning_rate: float = 0.001
    sequence_length: int = 20
    maximum_positions: int = 30
    exposure: float = 0.95
    buy_cost: float = 0.0005
    sell_cost: float = 0.001
    signal_threshold: float = 0.002
    soft_temperature: float = 0.002
    max_drawdown_limit: float = 0.20
    max_epochs: int = 120
    patience: int = 15
    seed: int = 42

    def validate(self) -> None:
        for name in (
            'hidden_size', 'num_layers', 'batch_size', 'sequence_length',
            'maximum_positions', 'max_epochs',
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f'{name} must be a positive integer')
        if self.maximum_positions != 30:
            raise ValueError('The portfolio research protocol uses exactly 30 position slots')
        if (isinstance(self.patience, bool) or not isinstance(self.patience, int)
                or self.patience < 0 or isinstance(self.seed, bool)
                or not isinstance(self.seed, int)):
            raise ValueError('patience and seed must be valid integers')
        if (not math.isfinite(self.learning_rate) or not 0 < self.learning_rate < 1
                or not math.isfinite(self.dropout) or not 0 <= self.dropout < 1
                or (self.num_layers == 1 and self.dropout != 0)):
            raise ValueError('Invalid optimizer learning rate or LSTM dropout')
        if (not math.isfinite(self.exposure) or not 0 < self.exposure <= 1
                or any(not math.isfinite(value) or not 0 <= value < 1
                       for value in (self.buy_cost, self.sell_cost))
                or not math.isfinite(self.signal_threshold)
                or not 0 < self.signal_threshold < 1
                or not math.isfinite(self.soft_temperature)
                or self.soft_temperature <= 0
                or not math.isfinite(self.max_drawdown_limit)
                or not 0 < self.max_drawdown_limit < 1):
            raise ValueError('Invalid portfolio exposure, costs, thresholds or drawdown limit')


class SharedPortfolioLSTM(nn.Module):
    """One LSTM shared by all stocks, returning one score per input sequence."""

    def __init__(self, feature_count: int, config: PortfolioModelConfig):
        super().__init__()
        config.validate()
        if feature_count != len(FEATURE_NAMES):
            raise ValueError('Feature count does not match the model feature schema')
        self.lstm = nn.LSTM(
            feature_count, config.hidden_size, num_layers=config.num_layers,
            batch_first=True, dropout=config.dropout,
        )
        self.output = nn.Linear(config.hidden_size, 1)

    def forward(self, values: Tensor) -> Tensor:
        if values.ndim != 3:
            raise ValueError('Model input must have shape [batch, time, feature]')
        sequence, _ = self.lstm(values)
        return self.output(sequence[:, -1]).squeeze(-1)


def wrap_model_for_training(
    model: SharedPortfolioLSTM,
    device: torch.device,
) -> nn.Module:
    if device.type == 'cuda' and torch.cuda.device_count() > 1:
        return nn.DataParallel(
            model, device_ids=list(range(torch.cuda.device_count())),
        )
    return model


def unwrap_shared_model(model: nn.Module) -> SharedPortfolioLSTM:
    if isinstance(model, nn.DataParallel):
        model = model.module
    if not isinstance(model, SharedPortfolioLSTM):
        raise ValueError('Expected a shared portfolio LSTM or its DataParallel wrapper')
    return model


def build_feature_frame(
    prices: pd.DataFrame,
    sessions: Sequence[date],
    weights: Sequence[float] | np.ndarray,
) -> pd.DataFrame:
    """Build causal features, restarting each filter after missing/suspended sessions."""
    required = {'date', 'open', 'high', 'low', 'close', 'volume'}
    if not required <= set(prices.columns) or prices.empty:
        raise ValueError(f'Prices require nonempty columns: {sorted(required)}')
    if 'suspended' not in prices.columns:
        prices = prices.assign(suspended=False)
    if not sessions:
        raise ValueError('Trading sessions must not be empty')
    normalized_sessions = [pd.Timestamp(day).date() for day in sessions]
    if (normalized_sessions != sorted(set(normalized_sessions))
            or any(not isinstance(day, date) for day in normalized_sessions)):
        raise ValueError('Trading sessions must be unique and sorted')
    session_index = {day: index for index, day in enumerate(normalized_sessions)}
    frame = prices.copy()
    frame['date'] = pd.to_datetime(frame['date'], errors='raise').dt.date
    if frame['date'].duplicated().any():
        raise ValueError('Duplicate price dates are not allowed')
    if not set(frame['date']) <= set(session_index):
        raise ValueError('Price dates must belong to the supplied trading calendar')
    numeric = ['open', 'high', 'low', 'close', 'volume']
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors='raise')
    values = frame[numeric].to_numpy(dtype=float)
    if (not np.isfinite(values).all() or (values[:, :4] <= 0).any()
            or (values[:, 4] <= 0).any()
            or (frame['low'] > frame[['open', 'close']].min(axis=1)).any()
            or (frame['high'] < frame[['open', 'close']].max(axis=1)).any()):
        raise ValueError('Invalid adjusted OHLCV values')
    suspension_values = frame['suspended'].fillna(False)
    if not suspension_values.isin((False, True, 0, 1)).all():
        raise ValueError('Suspension flags must be boolean or 0/1')
    frame['suspended'] = suspension_values.astype(bool)
    filter_weights = np.asarray(weights, dtype=float)
    if (filter_weights.ndim != 1 or not len(filter_weights)
            or filter_weights[0] != 1 or not np.isfinite(filter_weights).all()):
        raise ValueError('Fractional weights must be finite and start with lag-zero weight 1')
    frame['_session_index'] = frame['date'].map(session_index)
    frame = frame.sort_values('date').reset_index(drop=True)
    tradable = frame.loc[~frame['suspended']].copy().reset_index(drop=True)
    output = pd.DataFrame({
        'date': tradable['date'],
        **{name: np.nan for name in FEATURE_NAMES},
    })
    if tradable.empty:
        return output

    breaks = tradable['_session_index'].diff().fillna(1).ne(1)
    group_ids = breaks.cumsum()
    for _, segment in tradable.groupby(group_ids, sort=False):
        rows = segment.index.to_numpy()
        log_close = np.log(segment['close'].to_numpy(dtype=float))
        log_volume = np.log1p(segment['volume'].to_numpy(dtype=float))
        previous_close = np.roll(log_close, 1)
        previous_volume = np.roll(log_volume, 1)
        previous_close[0] = np.nan
        previous_volume[0] = np.nan
        features = np.column_stack((
            fractional_difference(log_close, filter_weights),
            log_close - previous_close,
            np.log(segment['high'].to_numpy() / segment['low'].to_numpy()),
            np.log(segment['open'].to_numpy()) - previous_close,
            log_volume - previous_volume,
        ))
        features[0, :] = np.nan
        output.loc[rows, list(FEATURE_NAMES)] = features
    if 'instrument' in tradable.columns:
        output['instrument'] = tradable['instrument'].to_numpy()
    output['close'] = tradable['close'].to_numpy()
    return output.reset_index(drop=True)


def fit_feature_scaler(training_sequences: np.ndarray) -> dict:
    """Fit one shared scaler from training sequences only."""
    values = np.asarray(training_sequences, dtype=np.float64)
    if values.ndim != 3 or values.shape[-1] != len(FEATURE_NAMES) or not values.size:
        raise ValueError('Training sequences must have shape [samples, time, features]')
    if not np.isfinite(values).all():
        raise ValueError('Training sequences must be finite')
    mean = values.reshape(-1, values.shape[-1]).mean(axis=0)
    scale = values.reshape(-1, values.shape[-1]).std(axis=0)
    scale = np.where(scale > 1e-8, scale, 1.0)
    return {'mean': mean.tolist(), 'scale': scale.tolist()}


def _validate_scaler(scaler: Mapping) -> tuple[np.ndarray, np.ndarray]:
    try:
        mean = np.asarray(scaler['mean'], dtype=np.float32)
        scale = np.asarray(scaler['scale'], dtype=np.float32)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('Invalid feature scaler') from exc
    if (mean.shape != (len(FEATURE_NAMES),) or scale.shape != mean.shape
            or not np.isfinite(mean).all() or not np.isfinite(scale).all()
            or (scale <= 0).any()):
        raise ValueError('Scaler must contain finite values for every model feature')
    return mean, scale


def select_positions(
    scores: Mapping[str, float],
    previous: Mapping[str, float],
    eligible: set[str],
    config: PortfolioModelConfig | None = None,
) -> dict[str, float]:
    """Select up to 30 equal-weight positions; inactive slots remain cash."""
    config = config or PortfolioModelConfig()
    config.validate()
    candidates = []
    for symbol, score in scores.items():
        if symbol not in eligible:
            continue
        if not math.isfinite(float(score)):
            raise ValueError(f'Non-finite model score for {symbol}')
        was_held = float(previous.get(symbol, 0.0)) > 0
        if float(score) > config.signal_threshold or (
            was_held and float(score) >= -config.signal_threshold
        ):
            candidates.append((symbol, float(score)))
    candidates.sort(key=lambda item: (-item[1], item[0]))
    slot_weight = config.exposure / config.maximum_positions
    return {symbol: slot_weight for symbol, _ in candidates[:config.maximum_positions]}


def make_position_targets(
    scores: Tensor,
    eligible: Tensor,
    previous: Tensor,
    config: PortfolioModelConfig,
) -> Tensor:
    """Differentiable occupancy approximation for the discrete 30-slot selector."""
    config.validate()
    if scores.shape != eligible.shape or scores.shape != previous.shape:
        raise ValueError('Scores, eligibility and prior weights must have equal shapes')
    if scores.ndim not in (1, 2):
        raise ValueError('Portfolio targets must have shape [stocks] or [days, stocks]')
    mask = eligible.to(dtype=scores.dtype)
    occupancy = torch.sigmoid(
        (scores - config.signal_threshold) / config.soft_temperature,
    ) * mask
    total = occupancy.sum(dim=-1, keepdim=True)
    capacity_scale = torch.clamp(
        config.maximum_positions / total.clamp_min(torch.finfo(scores.dtype).eps),
        max=1.0,
    )
    targets = occupancy * capacity_scale * (config.exposure / config.maximum_positions)
    return targets


def portfolio_growth_loss(
    scores: Tensor,
    returns: Tensor,
    eligible: Tensor,
    previous: Tensor,
    config: PortfolioModelConfig,
) -> Tensor:
    """Differentiable net-log-growth proxy, including asymmetric turnover costs."""
    if scores.shape != returns.shape:
        raise ValueError('Scores and next-period returns must have equal shapes')
    targets = make_position_targets(scores, eligible, previous, config)
    buys = torch.relu(targets - previous)
    sells = torch.relu(previous - targets)
    transaction_cost = config.buy_cost * buys.sum(dim=-1) + config.sell_cost * sells.sum(dim=-1)
    gross_return = (targets * returns).sum(dim=-1)
    net_return = gross_return - transaction_cost
    if not torch.isfinite(net_return).all() or (net_return <= -1).any():
        raise ValueError('Portfolio batch contains an invalid net return')
    return -torch.log1p(net_return).mean()


def train_shared_model(
    model: SharedPortfolioLSTM,
    training_batches: Sequence[Mapping[str, Tensor]],
    config: PortfolioModelConfig,
    validation_evaluator: Callable[[SharedPortfolioLSTM, int], Mapping] | None = None,
    validation_years: Sequence[str] | None = None,
) -> dict:
    """Fit shared model weights against portfolio-level net growth batches.

    Each batch supplies sequences [days, stocks, time, features], next returns,
    tradability masks, and prior weights, each latter array shaped [days, stocks].
    If supplied, validation_evaluator must run the separate portfolio simulation
    and return portfolio_return and positive max_drawdown_by_year fractions for
    exactly validation_years. The evaluator, not training loss, controls early
    stopping and checkpoint selection.
    """
    config.validate()
    if not training_batches:
        raise ValueError('At least one portfolio training batch is required')
    if validation_evaluator is not None and (
        not validation_years or len(set(validation_years)) != len(validation_years)
    ):
        raise ValueError('Validation selection requires a nonempty unique year list')
    torch.manual_seed(config.seed)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    history = []
    best_loss = float('inf')
    best_validation_return = float('-inf')
    best_epoch = None
    best_state = None
    patience_left = config.patience
    parameter = next(model.parameters())
    for epoch in range(config.max_epochs):
        model.train()
        losses = []
        prior_positions = None
        for batch in training_batches:
            sequences = batch['sequences'].to(
                device=parameter.device, dtype=parameter.dtype,
            )
            returns = batch['returns'].to(device=parameter.device, dtype=parameter.dtype)
            eligible = batch['eligible'].to(device=parameter.device, dtype=torch.bool)
            previous = batch['previous'].to(device=parameter.device, dtype=parameter.dtype)
            if (sequences.ndim != 4 or sequences.shape[2] != config.sequence_length
                    or sequences.shape[3] != len(FEATURE_NAMES)
                    or sequences.shape[:2] != returns.shape
                    or returns.shape != eligible.shape or returns.shape != previous.shape
                    or not torch.isfinite(sequences).all()
                    or not torch.isfinite(returns).all()
                    or not torch.isfinite(previous).all()):
                raise ValueError('Training batch shapes do not match portfolio model contract')
            day_count, stock_count = returns.shape
            raw_scores = model(sequences.reshape(
                day_count * stock_count, config.sequence_length, len(FEATURE_NAMES),
            )).reshape(day_count, stock_count)
            targets = make_position_targets(raw_scores, eligible, previous, config)
            initial_positions = previous[0] if prior_positions is None else prior_positions
            previous_by_day = torch.cat((
                initial_positions.unsqueeze(0), targets[:-1].detach(),
            ), dim=0)
            loss = portfolio_growth_loss(
                raw_scores, returns, eligible, previous_by_day, config,
            )
            if not torch.isfinite(loss):
                raise ValueError(f'Non-finite portfolio loss in epoch {epoch + 1}')
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().cpu()))
            prior_positions = targets[-1].detach()
        epoch_loss = float(np.mean(losses))
        history.append({'epoch': epoch + 1, 'training_loss': epoch_loss})
        best_loss = min(best_loss, epoch_loss)
        if validation_evaluator is None:
            continue
        model.eval()
        validation = validation_evaluator(model, epoch + 1)
        try:
            portfolio_return = float(validation['portfolio_return'])
            annual_drawdowns = validation['max_drawdown_by_year']
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise ValueError('Validation must return portfolio_return and yearly drawdowns') from exc
        if (not isinstance(annual_drawdowns, Mapping)
                or set(annual_drawdowns) != set(validation_years)):
            raise ValueError('Validation drawdowns must cover exactly the configured years')
        try:
            drawdown_values = [float(value) for value in annual_drawdowns.values()]
        except (TypeError, ValueError) as exc:
            raise ValueError('Validation must return portfolio_return and yearly drawdowns') from exc
        if (not math.isfinite(portfolio_return) or not drawdown_values
                or not all(math.isfinite(value) and 0 <= value <= 1
                           for value in drawdown_values)):
            raise ValueError('Validation results must contain finite yearly drawdowns in [0, 1]')
        passed = all(value <= config.max_drawdown_limit for value in drawdown_values)
        history[-1]['validation'] = {
            'portfolio_return': portfolio_return,
            'max_drawdown_by_year': dict(annual_drawdowns),
            'passed_drawdown_gate': passed,
        }
        if passed and portfolio_return > best_validation_return:
            best_validation_return = portfolio_return
            best_epoch = epoch + 1
            best_state = {
                name: value.detach().clone()
                for name, value in model.state_dict().items()
            }
            patience_left = config.patience
        elif config.patience and best_state is not None:
            patience_left -= 1
            if patience_left <= 0:
                break
    selected = best_state is not None
    if selected:
        model.load_state_dict(best_state)
    return {
        'minimum_training_loss': best_loss,
        'epochs_completed': len(history),
        'history': history,
        'best_validation_portfolio_return': (
            best_validation_return if selected else None
        ),
        'best_epoch': best_epoch,
        'selection_metric': (
            'validation_portfolio_return_subject_to_annual_drawdown_limit'
            if validation_evaluator is not None else 'not_selected_validation_required'
        ),
        'selected': selected,
        'validation_required_for_model_selection': not selected,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_bundle_inputs(
    model: SharedPortfolioLSTM,
    config: PortfolioModelConfig,
    symbols: Sequence[str],
    differencing_weights: Mapping[str, Sequence[float]],
    scaler: Mapping,
    universe_signature: str,
    metadata: Mapping,
) -> None:
    config.validate()
    if not isinstance(model, SharedPortfolioLSTM):
        raise ValueError('Bundle requires a shared portfolio LSTM')
    if (not symbols or len(set(symbols)) != len(symbols)
            or any(not isinstance(symbol, str) or not symbol for symbol in symbols)):
        raise ValueError('Bundle symbols must be a nonempty unique list')
    if set(differencing_weights) != set(symbols):
        raise ValueError('Differencing weights must cover exactly the model symbols')
    for symbol, weights in differencing_weights.items():
        values = np.asarray(weights, dtype=float)
        if (values.ndim != 1 or not len(values) or values[0] != 1
                or not np.isfinite(values).all()):
            raise ValueError(f'Invalid differencing weights for {symbol}')
    _validate_scaler(scaler)
    if (not isinstance(universe_signature, str) or len(universe_signature) != 64
            or any(char not in '0123456789abcdef' for char in universe_signature.lower())):
        raise ValueError('Universe signature must be a 64-character SHA256 hex digest')
    required_metadata = {'run_id', 'method', 'epoch', 'training_status', 'validation'}
    if not required_metadata <= set(metadata):
        raise ValueError(f'Model metadata is missing: {sorted(required_metadata - set(metadata))}')
    if metadata['method'] not in ('de_prado', 'log_return'):
        raise ValueError('Model metadata has an unsupported fractional-difference method')
    if not isinstance(metadata['validation'], Mapping):
        raise ValueError('Validation metadata must be an object')


def save_model_bundle(
    directory: Path,
    model: SharedPortfolioLSTM,
    config: PortfolioModelConfig,
    symbols: Sequence[str],
    differencing_weights: Mapping[str, Sequence[float]],
    scaler: Mapping,
    universe_signature: str,
    metadata: Mapping,
) -> Path:
    """Write an immutable, versioned model bundle; never overwrite existing output."""
    directory = Path(directory).resolve()
    _validate_bundle_inputs(
        model, config, symbols, differencing_weights, scaler,
        universe_signature, metadata,
    )
    if directory.exists():
        raise ValueError(f'Model bundle already exists: {directory}')
    directory.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f'.{directory.name}.', dir=directory.parent))
    try:
        state_path = staging / 'model.pt'
        torch.save(
            {name: value.detach().cpu().contiguous()
             for name, value in model.state_dict().items()},
            state_path,
        )
        manifest = {
            'bundle_version': MODEL_BUNDLE_VERSION,
            'model_type': 'shared_fractional_portfolio_lstm',
            'architecture': {'feature_count': len(FEATURE_NAMES)},
            'config': asdict(config),
            'feature_names': list(FEATURE_NAMES),
            'symbols': list(symbols),
            'differencing_weights': {
                symbol: [float(value) for value in differencing_weights[symbol]]
                for symbol in symbols
            },
            'scaler': {
                'mean': [float(value) for value in scaler['mean']],
                'scale': [float(value) for value in scaler['scale']],
            },
            'price_protocol': PRICE_PROTOCOL,
            'universe_signature': universe_signature,
            'state_dict_sha256': _sha256(state_path),
            'metadata': dict(metadata),
            'live_trading_eligible': False,
        }
        manifest_path = staging / 'manifest.json'
        with manifest_path.open('w', encoding='utf-8', newline='\n') as stream:
            json.dump(manifest, stream, ensure_ascii=True, indent=2, allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        if directory.exists():
            raise ValueError(f'Model bundle already exists: {directory}')
        staging.rename(directory)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return directory


@dataclass(frozen=True)
class LoadedModelBundle:
    model: SharedPortfolioLSTM
    config: PortfolioModelConfig
    manifest: dict
    directory: Path


def load_model_bundle(
    directory: Path,
    map_location: str | torch.device = 'cpu',
) -> LoadedModelBundle:
    directory = Path(directory).resolve()
    manifest_path = directory / 'manifest.json'
    state_path = directory / 'model.pt'
    try:
        with manifest_path.open('r', encoding='utf-8') as stream:
            manifest = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f'Unable to read model bundle manifest: {manifest_path}') from exc
    if manifest.get('bundle_version') != MODEL_BUNDLE_VERSION:
        raise ValueError('Unsupported model bundle version')
    if (manifest.get('model_type') != 'shared_fractional_portfolio_lstm'
            or manifest.get('feature_names') != list(FEATURE_NAMES)
            or manifest.get('architecture') != {'feature_count': len(FEATURE_NAMES)}
            or manifest.get('price_protocol') != PRICE_PROTOCOL):
        raise ValueError('Model bundle feature or price protocol is incompatible')
    if not state_path.is_file() or _sha256(state_path) != manifest.get('state_dict_sha256'):
        raise ValueError('Model state SHA256 does not match manifest')
    try:
        config = PortfolioModelConfig(**manifest['config'])
        config.validate()
        symbols = manifest['symbols']
        _validate_bundle_inputs(
            SharedPortfolioLSTM(len(FEATURE_NAMES), config), config, symbols,
            manifest['differencing_weights'], manifest['scaler'],
            manifest['universe_signature'], manifest['metadata'],
        )
        model = SharedPortfolioLSTM(len(FEATURE_NAMES), config)
        state = torch.load(state_path, map_location=map_location, weights_only=True)
        model.load_state_dict(state, strict=True)
        model.to(map_location)
        model.eval()
    except (KeyError, TypeError, RuntimeError) as exc:
        raise ValueError(f'Model bundle contents are invalid: {exc}') from exc
    return LoadedModelBundle(model, config, manifest, directory)


def predict_scores(
    bundle: LoadedModelBundle,
    prices_by_symbol: Mapping[str, pd.DataFrame],
    sessions: Sequence[date],
    as_of: date,
) -> tuple[dict[str, float], dict[str, str]]:
    """Batch score requested symbols as of a completed session, without trading."""
    normalized_sessions = [pd.Timestamp(day).date() for day in sessions]
    as_of = pd.Timestamp(as_of).date()
    if as_of not in normalized_sessions:
        raise ValueError('as_of must be a session in the supplied calendar')
    unknown = set(prices_by_symbol) - set(bundle.manifest['symbols'])
    if unknown:
        raise ValueError(f'unknown model symbols: {sorted(unknown)}')
    mean, scale = _validate_scaler(bundle.manifest['scaler'])
    sequences, symbols, exclusions = [], [], {}
    for symbol in set(bundle.manifest['symbols']) - set(prices_by_symbol):
        exclusions[symbol] = 'no price frame supplied'
    for symbol, prices in prices_by_symbol.items():
        frame = prices.copy()
        if 'date' not in frame.columns:
            raise ValueError(f'Price frame has no date column for {symbol}')
        frame['date'] = pd.to_datetime(frame['date'], errors='raise').dt.date
        if not (frame['date'] == as_of).any() or (
            'suspended' in frame.columns
            and frame.loc[frame['date'] == as_of, 'suspended'].fillna(False).astype(bool).all()
        ):
            exclusions[symbol] = 'no tradable quote on as_of session'
            continue
        features = build_feature_frame(
            frame[frame['date'] <= as_of], normalized_sessions,
            bundle.manifest['differencing_weights'][symbol],
        )
        last = features.loc[features['date'] == as_of, list(FEATURE_NAMES)]
        if len(last) != 1 or last.isna().any(axis=None):
            exclusions[symbol] = 'insufficient contiguous finite feature history'
            continue
        finite_features = features[list(FEATURE_NAMES)].to_numpy(dtype=np.float32)
        finite_rows = np.flatnonzero(np.isfinite(finite_features).all(axis=1))
        end = len(features) - 1
        if (not len(finite_rows) or finite_rows[-1] != end
                or end + 1 < bundle.config.sequence_length):
            exclusions[symbol] = 'insufficient contiguous finite feature history'
            continue
        start = end - bundle.config.sequence_length + 1
        sequence = finite_features[start:end + 1]
        if not np.isfinite(sequence).all():
            exclusions[symbol] = 'insufficient contiguous finite feature history'
            continue
        sequences.append((sequence - mean) / scale)
        symbols.append(symbol)
    if not sequences:
        return {}, exclusions
    parameter = next(bundle.model.parameters())
    batch = torch.as_tensor(np.stack(sequences), dtype=parameter.dtype, device=parameter.device)
    with torch.inference_mode():
        values = bundle.model(batch).detach().cpu().numpy()
    if not np.isfinite(values).all():
        raise ValueError('Model produced non-finite inference scores')
    return dict(zip(symbols, values.astype(float).tolist())), exclusions
