"""按时间顺序训练和评估 LSTM 预测模型的研究实验。

训练、验证和测试数据按目标日期切分。验证标签只用于模型选择，不参与梯度更新；
测试开始前用训练和验证数据重新拟合，测试数据只用于预测评分。该模块用于研究
预测误差，不直接连接交易账户，也不应把测试集表现解释为未来收益保证。
"""

from dataclasses import asdict, dataclass
from datetime import date
import logging
from math import exp
import os
from pathlib import Path
import time
from typing import Sequence

import numpy as np
import pandas as pd
from market_data.price_basis import (
    ADJUSTED_BASIS, PRICE_COLUMNS, frame_digest, research_price_contract,
)

logger = logging.getLogger(__name__)

from research.fractional_forecast import (
    DifferencingError, ForecastConfig, estimate_order, forecast_features,
    fractional_difference, fractional_weights, invert_one_step, validate_prices,
)
from research.prediction_metrics import evaluate_return_predictions as _evaluate_returns


@dataclass(frozen=True)
class LSTMTrial:
    hidden_size: int = 16
    learning_rate: float = 0.001
    epochs: int = 30
    batch_size: int = 64
    num_layers: int = 1
    dropout: float = 0.0

    def validate(self) -> None:
        for value in (self.hidden_size, self.epochs, self.batch_size, self.num_layers):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise DifferencingError('LSTM sizes and epochs must be positive integers')
        if not np.isfinite(self.learning_rate) or not 0 < self.learning_rate < 1:
            raise DifferencingError('Invalid LSTM learning rate')
        if (not np.isfinite(self.dropout) or not 0 <= self.dropout < 1
                or (self.num_layers == 1 and self.dropout != 0)):
            raise DifferencingError('Dropout requires multiple layers and a rate in [0, 1)')


@dataclass
class EarlyStopping:
    patience: int = 15
    min_delta: float = 1e-6
    best_score: float = float('inf')
    best_epoch: int = 0
    significant_best: float = float('inf')
    wait: int = 0

    def __post_init__(self):
        if (isinstance(self.patience, bool) or not isinstance(self.patience, int)
                or self.patience < 0 or not np.isfinite(self.min_delta)
                or self.min_delta < 0):
            raise DifferencingError('Invalid early-stopping patience or min_delta')

    def observe(self, score: float, epoch: int) -> tuple[bool, bool]:
        if not np.isfinite(score):
            raise DifferencingError('Non-finite validation selection score')
        improved = score < self.best_score
        if improved:
            self.best_score, self.best_epoch = score, epoch
        if score < self.significant_best - self.min_delta:
            self.significant_best, self.wait = score, 0
        else:
            self.wait += 1
        return improved, self.patience > 0 and self.wait >= self.patience


def training_device(device_index: int | None = None):
    os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
    import torch

    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    count = torch.cuda.device_count() if torch.cuda.is_available() else 0
    if device_index is not None:
        if (isinstance(device_index, bool) or not isinstance(device_index, int)
                or not 0 <= device_index < count):
            raise DifferencingError(f'GPU index {device_index} unavailable; found {count}')
        torch.cuda.set_device(device_index)
    return torch.device(f'cuda:{device_index or 0}' if count else 'cpu')


def build_network(features: int, trial: LSTMTrial):
    from torch import nn

    trial.validate()

    class Network(nn.Module):
        def __init__(self):
            super().__init__()
            self.lstm = nn.LSTM(
                features, trial.hidden_size, num_layers=trial.num_layers,
                batch_first=True, dropout=trial.dropout,
            )
            self.output = nn.Linear(trial.hidden_size, 1)

        def forward(self, values):
            sequence, _ = self.lstm(values)
            return self.output(sequence[:, -1]).squeeze(-1)

    return Network()


def return_context(data: dict, indices: np.ndarray, mean: float, scale: float) -> dict:
    origins = data['origins'][indices]
    offsets = [
        invert_one_step(0.0, data['logs'][:origin + 1], data['weights'])
        - data['logs'][origin] for origin in origins
    ]
    return {
        'offsets': np.asarray(offsets),
        'actual': np.expm1(data['logs'][origins + 1] - data['logs'][origins]),
        'mean': mean, 'scale': scale,
    }


def reconstructed_returns(outputs: np.ndarray, context: dict) -> np.ndarray:
    with np.errstate(over='ignore', invalid='ignore'):
        values = np.expm1(
            np.asarray(outputs, dtype=float) * context['scale']
            + context['mean'] + context['offsets'],
        )
    if not np.isfinite(values).all():
        raise DifferencingError('Non-finite reconstructed return predictions')
    return values


def fit_trial(
    x, y, train_indices, validation_indices, trial: LSTMTrial, *,
    seed: int = 42, patience: int = 0, min_delta: float = 1e-6,
    context: dict | None = None, use_data_parallel: bool = False,
    on_improvement=None,
) -> dict:
    """Fit one candidate; selection labels never enter gradient updates."""
    import torch
    from torch import nn

    trial.validate()
    stopping = EarlyStopping(patience, min_delta)
    if not len(train_indices) or not len(validation_indices):
        raise DifferencingError('Training and validation samples must be nonempty')
    if set(train_indices.cpu().tolist()) & set(validation_indices.cpu().tolist()):
        raise DifferencingError('Training and validation indices overlap')
    torch.manual_seed(seed)
    model = build_network(x.shape[-1], trial).to(x.device)
    if use_data_parallel:
        model = nn.DataParallel(model, device_ids=[0, 1])
    optimizer = torch.optim.Adam(model.parameters(), lr=trial.learning_rate)
    history, best = [], None
    for epoch in range(1, trial.epochs + 1):
        model.train()
        training_loss_sum = torch.zeros((), device=x.device)
        for batch in train_indices.split(trial.batch_size):
            optimizer.zero_grad()
            loss = nn.functional.mse_loss(model(x[batch]), y[batch])
            if not torch.isfinite(loss):
                raise DifferencingError('Non-finite LSTM training loss')
            training_loss_sum += loss.detach() * len(batch)
            loss.backward()
            optimizer.step()
        model.eval()
        with torch.no_grad():
            outputs = model(x[validation_indices])
            mse = float(nn.functional.mse_loss(outputs, y[validation_indices]).item())
        if not np.isfinite(mse):
            raise DifferencingError('Non-finite LSTM validation loss')
        score = mse if context is None else float(np.mean(np.abs(
            reconstructed_returns(outputs.cpu().numpy(), context) - context['actual'],
        )))
        improved, stop = stopping.observe(score, epoch)
        history.append({
            'epoch': epoch,
            'training_mse_scaled': float((training_loss_sum / len(train_indices)).item()),
            'validation_mse_scaled': mse, 'selection_score': score,
        })
        if improved:
            unwrapped = model.module if use_data_parallel else model
            best = {
                'model': {k: v.detach().cpu().clone()
                          for k, v in unwrapped.state_dict().items()},
                'epoch': epoch, 'validation_mse_scaled': mse,
                'selection_score': score,
            }
            if on_improvement is not None:
                on_improvement({**best, 'epoch_history': list(history)})
        if stop:
            break
    if best is None:
        raise DifferencingError('No finite model checkpoint selected')
    return {
        **best, 'epoch_history': history,
        'stopped_early': len(history) < trial.epochs,
        'selection_metric': 'scaled_mse' if context is None else 'return_mae',
    }


def atomic_replace(temporary: Path, destination: Path) -> None:
    for attempt in range(6):
        try:
            os.replace(temporary, destination)
            return
        except PermissionError as exc:
            # Windows scanners may briefly hold a just-written checkpoint open.
            if getattr(exc, 'winerror', None) not in (5, 32, 33) or attempt == 5:
                raise
            logger.warning('Checkpoint replace locked; retrying %s (%d/5)',
                           destination, attempt + 1)
            time.sleep(0.05 * 2 ** attempt)


def save_training_checkpoint(path: Path, payload: dict) -> None:
    import torch

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('wb') as stream:
        torch.save({
            **payload, 'checkpoint_version': 1,
            'price_contract': research_price_contract(),
        }, stream)
        stream.flush()
        os.fsync(stream.fileno())
    atomic_replace(temporary, path)


def load_training_checkpoint(path: Path):
    import torch

    payload = torch.load(path, map_location='cpu', weights_only=True)
    if (payload.get('checkpoint_version') != 1
            or payload.get('price_contract') != research_price_contract()):
        raise DifferencingError('Incompatible training checkpoint or price contract')
    model = build_network(payload['feature_count'], LSTMTrial(**payload['trial']))
    model.load_state_dict(payload['model'])
    return payload, model


def prepare_sequences(
    frame: pd.DataFrame, config: ForecastConfig, order: float,
) -> dict:
    """构造一步预测序列，并按目标日期划分训练、验证和测试集。

    每个样本的输入特征最晚截至起点 t，标签是 t+1；边界按标签日期判断，
    避免跨期序列因起点在训练区间而把验证/测试目标混入训练集。验证标签只在
    训练完成后用于评估和选 epoch，不进入训练梯度；此处缩放参数仅由训练期计算。
    """
    config.validate()
    frame = validate_prices(frame)
    if frame['instrument'].nunique() != 1:
        raise DifferencingError('Sequences require one stock')
    logs = np.log(frame['close'].to_numpy(dtype=float))
    weights = fractional_weights(order, config.weight_threshold, config.max_lags)
    transformed = fractional_difference(logs, weights)
    features = forecast_features(frame['close'], transformed).to_numpy(dtype=float)
    days = frame['date'].tolist()
    sequences, targets, origins, target_days = [], [], [], []
    for origin in range(config.sequence_length - 1, len(frame) - 1):
        sequence = features[origin - config.sequence_length + 1:origin + 1]
        target = transformed[origin + 1]
        if np.isfinite(sequence).all() and np.isfinite(target):
            sequences.append(sequence)
            targets.append(target)
            origins.append(origin)
            target_days.append(days[origin + 1])
    if not sequences:
        raise DifferencingError('No finite forecast sequences after warm-up')
    x = np.asarray(sequences)
    y = np.asarray(targets)
    train = np.asarray([
        config.train_start <= day < config.validation_start for day in target_days
    ])
    validation = np.asarray([
        config.validation_start <= day < config.test_start for day in target_days
    ])
    test = np.asarray([config.test_start <= day <= config.test_end for day in target_days])
    if train.sum() < config.minimum_train_samples:
        raise DifferencingError(f'Insufficient training samples: {train.sum()}')
    if validation.sum() < config.minimum_validation_samples:
        raise DifferencingError(f'Insufficient validation samples: {validation.sum()}')
    # 先按特征所属日期筛出训练期的原始特征行，再估算标准化参数；
    # 不直接对重叠序列求均值，以免重复计数，也不让验证/测试期统计量泄漏进来。
    feature_train = np.asarray([
        config.train_start <= day < config.validation_start for day in days
    ]) & np.isfinite(features).all(axis=1)
    x_mean = features[feature_train].mean(axis=0)
    x_scale = features[feature_train].std(axis=0)
    x_scale[x_scale < 1e-12] = 1.0
    y_mean, y_scale = float(y[train].mean()), float(y[train].std())
    if y_scale < 1e-12:
        raise DifferencingError('Training targets are constant')
    return {
        'x': ((x - x_mean) / x_scale).astype(np.float32),
        'y': ((y - y_mean) / y_scale).astype(np.float32),
        'raw_x': x, 'raw_y': y, 'features': features,
        'train': train, 'validation': validation, 'test': test,
        'origins': np.asarray(origins), 'target_dates': target_days, 'dates': days,
        'logs': logs, 'weights': weights,
        'x_mean': x_mean, 'x_scale': x_scale, 'y_mean': y_mean, 'y_scale': y_scale,
    }


def evaluate_return_predictions(
    actual_returns: Sequence[float], predicted_returns: Sequence[float],
) -> dict:
    """Summarize out-of-sample return prediction errors and direction accuracy."""
    try:
        return _evaluate_returns(actual_returns, predicted_returns)
    except ValueError as exc:
        raise DifferencingError(str(exc)) from exc


def train_stock(
    frame: pd.DataFrame, config: ForecastConfig, method: str,
    trials: Sequence[LSTMTrial] | None = None, seed: int = 42,
    walk_forward_validation_days: int = 60,
    device_index: int | None = None,
    patience: int = 0, min_delta: float = 1e-6,
    selection_metric: str = 'scaled_mse',
    checkpoint_directory: Path | None = None,
) -> tuple[dict, dict[tuple[date, str], float]]:
    """逐预测日执行滚动选型、历史重训和下一交易日预测。"""
    config.validate()
    EarlyStopping(patience, min_delta)
    if selection_metric not in ('scaled_mse', 'return_mae'):
        raise DifferencingError('Unknown LSTM selection metric')
    if frame.attrs.get('price_basis', ADJUSTED_BASIS) != ADJUSTED_BASIS:
        raise DifferencingError('LSTM requires adjusted research prices, not execution OHLC')
    if (isinstance(walk_forward_validation_days, bool)
            or not isinstance(walk_forward_validation_days, int)
            or walk_forward_validation_days < config.minimum_validation_samples):
        raise DifferencingError(
            'walk_forward_validation_days must be at least minimum_validation_samples',
        )
    frame = validate_prices(frame)
    frame = frame[(frame['date'] >= config.train_start) & (frame['date'] <= config.test_end)]
    if frame.empty:
        raise DifferencingError('No prices in configured training/test range')
    symbol = str(frame['instrument'].iloc[0])
    if frame['instrument'].nunique() != 1:
        raise DifferencingError('train_stock requires exactly one instrument')
    if method == 'log_return':
        order, order_details = 1.0, {'order': 1.0, 'estimation': 'fixed_first_difference'}
    elif method == 'de_prado':
        training = frame[frame['date'] < config.validation_start]
        order_details = estimate_order(np.log(training['close'].to_numpy()), config)
        order = order_details['order']
    else:
        raise DifferencingError('Supported methods are log_return and de_prado')
    data = prepare_sequences(frame, config, order)
    trials = list(trials) if trials is not None else [
        LSTMTrial(hidden_size=16), LSTMTrial(hidden_size=32),
    ]
    if not trials:
        raise DifferencingError('At least one explicit LSTM trial is required')
    for trial in trials:
        trial.validate()

    device = training_device(device_index)
    import torch
    from torch import nn

    gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 0

    loss_function = nn.MSELoss()

    def fit(
        x: torch.Tensor, y: torch.Tensor,
        train_indices: torch.Tensor, validation_indices: torch.Tensor,
        use_data_parallel: bool,
    ) -> tuple[dict, float, dict, list]:
        best_state = None
        best_validation_loss = float('inf')
        best_score = float('inf')
        selected_trial = None
        trial_results = []
        for trial_index, trial in enumerate(trials):
            result = fit_trial(
                x, y, train_indices, validation_indices, trial,
                seed=seed, patience=patience, min_delta=min_delta,
                context=selection_context, use_data_parallel=use_data_parallel,
            )
            if result['selection_score'] < best_score:
                best_score = result['selection_score']
                best_validation_loss = result['validation_mse_scaled']
                selected_trial = {
                    'trial_index': trial_index, 'epoch': result['epoch'],
                    **asdict(trial), 'selection_score': best_score,
                    'selection_metric': result['selection_metric'],
                }
                best_state = result['model']
            trial_results.append({
                'trial': asdict(trial),
                'last_validation_mse_scaled': result['epoch_history'][-1]['validation_mse_scaled'],
                'epoch_history': result['epoch_history'],
                'stopped_early': result['stopped_early'],
            })
        if best_state is None or selected_trial is None:
            raise DifferencingError('No trained model selected')
        return best_state, best_validation_loss, selected_trial, trial_results

    forecast_indices = np.flatnonzero(data['test'])
    if not len(forecast_indices):
        raise DifferencingError('No test forecast dates in configured interval')
    predictions = {}
    price_errors = []
    daily_selections = []
    selection_counts = {str(index): 0 for index in range(len(trials))}
    used_data_parallel_any = False
    gpu_oom_fallback_any = False
    started_at = time.perf_counter()
    logger.info(
        f'[{device}] Starting {symbol} {method}: '
        f'{len(forecast_indices)} walk-forward predictions',
    )
    last_model = None
    last_scaler = None
    last_metadata = None
    last_loss = None
    last_results = None
    last_fit_count = 0

    for sample_index in forecast_indices:
        target_day = data['target_dates'][sample_index]
        history_indices = np.asarray([
            index for index, day in enumerate(data['target_dates']) if day < target_day
        ], dtype=int)
        validation_indices_array = history_indices[-walk_forward_validation_days:]
        train_indices_array = history_indices[:-walk_forward_validation_days]
        if (len(train_indices_array) < config.minimum_train_samples
                or len(validation_indices_array) < config.minimum_validation_samples):
            raise DifferencingError(
                f'Insufficient pre-{target_day} history for walk-forward training: '
                f'{len(train_indices_array)} train, {len(validation_indices_array)} validation samples',
            )

        validation_start_day = data['target_dates'][validation_indices_array[0]]
        selection_features = np.asarray([
            config.train_start <= day < validation_start_day for day in data['dates']
        ]) & np.isfinite(data['features']).all(axis=1)
        selection_x_mean = data['features'][selection_features].mean(axis=0)
        selection_x_scale = data['features'][selection_features].std(axis=0)
        selection_x_scale[selection_x_scale < 1e-12] = 1.0
        selection_y_mean = float(data['raw_y'][train_indices_array].mean())
        selection_y_scale = float(data['raw_y'][train_indices_array].std())
        if selection_y_scale < 1e-12:
            raise DifferencingError(f'Pre-{target_day} training targets are constant')
        selection_x = torch.from_numpy(
            ((data['raw_x'] - selection_x_mean) / selection_x_scale).astype(np.float32),
        ).to(device)
        selection_y = torch.from_numpy(
            ((data['raw_y'] - selection_y_mean) / selection_y_scale).astype(np.float32),
        ).to(device)
        train_indices = torch.from_numpy(train_indices_array).to(device)
        validation_indices = torch.from_numpy(validation_indices_array).to(device)
        selection_context = (
            return_context(
                data, validation_indices_array, selection_y_mean, selection_y_scale,
            ) if selection_metric == 'return_mae' else None
        )

        used_data_parallel = False
        try:
            best_model, best_loss, best_metadata, results = fit(
                selection_x, selection_y, train_indices, validation_indices,
                use_data_parallel=False,
            )
        except torch.cuda.OutOfMemoryError as exc:
            if device_index is not None or gpu_count < 2:
                raise DifferencingError(
                    f'LSTM ran out of memory before {target_day}; '
                    'reduce the batch size or model size; parallel GPU workers do not share devices',
                ) from exc
            gpu_oom_fallback_any = True
            torch.cuda.empty_cache()
            try:
                best_model, best_loss, best_metadata, results = fit(
                    selection_x, selection_y, train_indices, validation_indices,
                    use_data_parallel=True,
                )
                used_data_parallel = True
                used_data_parallel_any = True
            except torch.cuda.OutOfMemoryError as fallback_exc:
                raise DifferencingError(
                    f'LSTM ran out of memory on both GPUs before {target_day}; '
                    'reduce the batch size or model size',
                ) from fallback_exc

        refit_feature_mask = np.asarray([
            config.train_start <= day < target_day for day in data['dates']
        ]) & np.isfinite(data['features']).all(axis=1)
        x_mean = data['features'][refit_feature_mask].mean(axis=0)
        x_scale = data['features'][refit_feature_mask].std(axis=0)
        x_scale[x_scale < 1e-12] = 1.0
        y_mean = float(data['raw_y'][history_indices].mean())
        y_scale = float(data['raw_y'][history_indices].std())
        if y_scale < 1e-12:
            raise DifferencingError(f'Pre-{target_day} refit targets are constant')
        x = torch.from_numpy(
            ((data['raw_x'] - x_mean) / x_scale).astype(np.float32),
        ).to(device)
        y = torch.from_numpy(
            ((data['raw_y'] - y_mean) / y_scale).astype(np.float32),
        ).to(device)

        final_trial = trials[int(best_metadata['trial_index'])]
        torch.manual_seed(seed)
        final_model = build_network(x.shape[-1], final_trial).to(device)
        if used_data_parallel:
            final_model = nn.DataParallel(final_model, device_ids=[0, 1])
        optimizer = torch.optim.Adam(final_model.parameters(), lr=final_trial.learning_rate)
        refit_indices = torch.from_numpy(history_indices)
        refit_indices = refit_indices.to(device)
        for _ in range(int(best_metadata['epoch'])):
            final_model.train()
            for batch in refit_indices.split(final_trial.batch_size):
                inputs = x[batch]
                targets = y[batch]
                optimizer.zero_grad()
                loss = loss_function(final_model(inputs), targets)
                if not torch.isfinite(loss):
                    raise DifferencingError(f'Non-finite refit loss before {target_day} for {symbol}')
                loss.backward()
                optimizer.step()
        final_model.eval()
        with torch.no_grad():
            output = float(final_model(x[sample_index:sample_index + 1]).item())
        prediction = output * y_scale + y_mean
        origin = int(data['origins'][sample_index])
        log_price = invert_one_step(
            float(prediction), data['logs'][:origin + 1], data['weights'],
        )
        predicted_return = exp(log_price - data['logs'][origin]) - 1
        if not np.isfinite(predicted_return):
            raise DifferencingError(f'Invalid inverse forecast for {symbol} on {target_day}')
        origin_day = data['dates'][origin]
        predictions[(origin_day, symbol)] = predicted_return
        actual_return = exp(data['logs'][origin + 1] - data['logs'][origin]) - 1
        price_errors.append(abs(predicted_return - actual_return))

        unwrapped = final_model.module if isinstance(final_model, nn.DataParallel) else final_model
        last_model = {
            name: value.detach().cpu().clone()
            for name, value in unwrapped.state_dict().items()
        }
        last_scaler = {
            'x_mean': x_mean.tolist(), 'x_scale': x_scale.tolist(),
            'y_mean': y_mean, 'y_scale': y_scale,
        }
        if checkpoint_directory is not None:
            common = {
                'instrument': symbol, 'method': method,
                'trial': asdict(final_trial), 'feature_count': int(x.shape[-1]),
                'weights': data['weights'].tolist(), 'seed': seed,
                'target_date': target_day.isoformat(),
                'config': {k: v.isoformat() if isinstance(v, date) else v
                           for k, v in asdict(config).items()},
                'selected_model': best_metadata,
                'selection_metric': selection_metric,
                'early_stopping_patience': patience, 'min_delta': min_delta,
                'selected_prices_sha256': frame_digest(
                    frame[frame['date'] < target_day], PRICE_COLUMNS,
                ),
            }
            destination = Path(checkpoint_directory) / f'{symbol}-{method}'
            save_training_checkpoint(destination / 'validation-best.pt', {
                **common, 'kind': 'validation_selection', 'model': best_model,
                'scaler': {
                    'x_mean': selection_x_mean.tolist(),
                    'x_scale': selection_x_scale.tolist(),
                    'y_mean': selection_y_mean, 'y_scale': selection_y_scale,
                },
                'validation_start': validation_start_day.isoformat(),
            })
            save_training_checkpoint(destination / 'refit-latest.pt', {
                **common, 'kind': 'pre_target_refit', 'model': last_model,
                'scaler': last_scaler, 'final_fit_samples': len(history_indices),
            })
        last_metadata, last_loss, last_results = best_metadata, best_loss, results
        last_fit_count = len(history_indices)
        selection_counts[str(best_metadata['trial_index'])] += 1
        daily_selections.append({
            'target_date': target_day.isoformat(),
            'train_samples': len(train_indices_array),
            'validation_start': validation_start_day.isoformat(),
            'validation_samples': len(validation_indices_array),
            'selected_trial': int(best_metadata['trial_index']),
            'selected_epoch': int(best_metadata['epoch']),
            'validation_mse_scaled': best_loss,
        })
        completed = len(predictions)
        if completed % 100 == 0 or completed == len(forecast_indices):
            elapsed = time.perf_counter() - started_at
            rate = completed / elapsed if elapsed > 0 else 0.0
            remaining = (len(forecast_indices) - completed) / rate if rate > 0 else 0.0
            logger.info(
                f'[{device}] {symbol} {method}: {completed}/{len(forecast_indices)} '
                f'predictions; latest={target_day}; elapsed={elapsed / 60:.1f}m; '
                f'estimated_remaining={remaining / 60:.1f}m',
            )

    if last_model is None or last_metadata is None or last_scaler is None:
        raise DifferencingError('No walk-forward model was trained')
    metadata = {
        'price_contract': research_price_contract(),
        'instrument': symbol, 'method': method, 'order_details': order_details,
        'sample_counts': {
            'train': last_fit_count - walk_forward_validation_days,
            'validation': walk_forward_validation_days,
            'test': len(forecast_indices),
        },
        'final_fit_samples': last_fit_count,
        'walk_forward_validation_days': walk_forward_validation_days,
        'walk_forward_prediction_count': len(forecast_indices),
        'walk_forward_trial_selection_counts': selection_counts,
        'daily_selections': daily_selections,
        'selected_model': last_metadata, 'validation_mse_scaled': last_loss,
        'selection_metric': selection_metric, 'early_stopping_patience': patience,
        'min_delta': min_delta,
        'checkpoint_directory': str(checkpoint_directory) if checkpoint_directory else None,
        'test_return_mae': float(np.mean(price_errors)) if price_errors else None,
        'trials': last_results, 'seed': seed,
        'training_device': str(device),
        'visible_gpu_count': gpu_count,
        'gpu_names': [torch.cuda.get_device_name(index) for index in range(gpu_count)],
        'data_parallel_gpus': [0, 1] if used_data_parallel_any else [],
        'gpu_oom_fallback': gpu_oom_fallback_any,
        'model': {name: tensor.tolist() for name, tensor in last_model.items()},
        'scaler': last_scaler,
        'weights': data['weights'].tolist(),
        'config': {name: value.isoformat() if isinstance(value, date) else value
                   for name, value in asdict(config).items()},
    }
    return metadata, predictions
