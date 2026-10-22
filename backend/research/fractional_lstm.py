"""按时间顺序训练和评估 LSTM 预测模型的研究实验。

训练、验证和测试数据按目标日期切分。验证标签只用于模型选择，不参与梯度更新；
测试开始前用训练和验证数据重新拟合，测试数据只用于预测评分。该模块用于研究
预测误差，不直接连接交易账户，也不应把测试集表现解释为未来收益保证。
"""

from dataclasses import asdict, dataclass
from datetime import date
import logging
from math import exp
import time
from typing import Sequence

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

from research.fractional_forecast import (
    DifferencingError, ForecastConfig, estimate_order, forecast_features,
    fractional_difference, fractional_weights, invert_one_step, validate_prices,
)


@dataclass(frozen=True)
class LSTMTrial:
    hidden_size: int = 16
    learning_rate: float = 0.001
    epochs: int = 30
    batch_size: int = 64

    def validate(self) -> None:
        for value in (self.hidden_size, self.epochs, self.batch_size):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise DifferencingError('LSTM sizes and epochs must be positive integers')
        if not np.isfinite(self.learning_rate) or not 0 < self.learning_rate < 1:
            raise DifferencingError('Invalid LSTM learning rate')


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


def train_stock(
    frame: pd.DataFrame, config: ForecastConfig, method: str,
    trials: Sequence[LSTMTrial] | None = None, seed: int = 42,
    walk_forward_validation_days: int = 60,
    device_index: int | None = None,
) -> tuple[dict, dict[tuple[date, str], float]]:
    """逐预测日执行滚动选型、历史重训和下一交易日预测。"""
    config.validate()
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

    import os

    # 在导入 PyTorch 前设置 CUDA 确定性配置，并保持统计库先于 PyTorch 加载，
    # 以降低 Intel OpenMP 运行库冲突风险；CUDA 初始化后再设置将不会生效。
    os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
    import torch
    from torch import nn

    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
    if device_index is None:
        device = torch.device('cuda:0' if gpu_count else 'cpu')
    else:
        if (isinstance(device_index, bool) or not isinstance(device_index, int)
                or device_index < 0 or device_index >= gpu_count):
            raise DifferencingError(
                f'GPU index {device_index} is unavailable; detected {gpu_count} CUDA devices',
            )
        device = torch.device(f'cuda:{device_index}')
        torch.cuda.set_device(device)

    class Network(nn.Module):
        def __init__(self, features: int, hidden: int):
            super().__init__()
            self.lstm = nn.LSTM(features, hidden, batch_first=True)
            self.output = nn.Linear(hidden, 1)

        def forward(self, values):
            sequence, _ = self.lstm(values)
            return self.output(sequence[:, -1]).squeeze(-1)

    loss_function = nn.MSELoss()

    def fit(
        x: torch.Tensor, y: torch.Tensor,
        train_indices: torch.Tensor, validation_indices: torch.Tensor,
        use_data_parallel: bool,
    ) -> tuple[dict, float, dict, list]:
        best_state = None
        best_validation_loss = float('inf')
        selected_trial = None
        trial_results = []
        for trial_index, trial in enumerate(trials):
            torch.manual_seed(seed)
            model = Network(x.shape[-1], trial.hidden_size).to(device)
            if use_data_parallel:
                model = nn.DataParallel(model, device_ids=[0, 1])
            optimizer = torch.optim.Adam(model.parameters(), lr=trial.learning_rate)
            validation_loss = float('inf')
            for epoch in range(trial.epochs):
                model.train()
                for batch in train_indices.split(trial.batch_size):
                    inputs = x[batch]
                    targets = y[batch]
                    optimizer.zero_grad()
                    loss = loss_function(model(inputs), targets)
                    if not torch.isfinite(loss):
                        raise DifferencingError(f'Non-finite training loss for {symbol}')
                    loss.backward()
                    optimizer.step()
                model.eval()
                validation_inputs = x[validation_indices]
                # 验证标签只计算留出误差以选模型/epoch，不参与反向传播。
                with torch.no_grad():
                    validation_loss = float(loss_function(
                        model(validation_inputs), y[validation_indices],
                    ).item())
                if not np.isfinite(validation_loss):
                    raise DifferencingError(f'Non-finite validation loss for {symbol}')
                if validation_loss < best_validation_loss:
                    best_validation_loss = validation_loss
                    selected_trial = {
                        'trial_index': trial_index, 'epoch': epoch + 1, **asdict(trial),
                    }
                    unwrapped = model.module if isinstance(model, nn.DataParallel) else model
                    best_state = {
                        name: value.detach().cpu().clone()
                        for name, value in unwrapped.state_dict().items()
                    }
            trial_results.append({
                'trial': asdict(trial),
                'last_validation_mse_scaled': validation_loss,
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
        final_model = Network(x.shape[-1], final_trial.hidden_size).to(device)
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
