"""按时间顺序训练和评估 LSTM 预测模型的研究实验。

训练、验证和测试数据按目标日期切分，标准化参数仅从训练期计算；模型参数、
随机种子和运行结果会保留，以便复现实验。该模块用于研究预测误差，不直接连接
交易账户，也不应把测试集表现解释为未来收益保证。
"""

from dataclasses import asdict, dataclass
from datetime import date
from math import exp
from typing import Sequence

import numpy as np
import pandas as pd

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
    避免跨期序列因起点在训练区间而把验证/测试目标混入训练集。均值和标准差
    仅由训练期间的特征行及标签计算，并返回供后续复用的缩放参数。
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
        'train': train, 'validation': validation, 'test': test,
        'origins': np.asarray(origins), 'target_dates': target_days, 'dates': days,
        'logs': logs, 'weights': weights,
        'x_mean': x_mean, 'x_scale': x_scale, 'y_mean': y_mean, 'y_scale': y_scale,
    }


def train_stock(
    frame: pd.DataFrame, config: ForecastConfig, method: str,
    trials: Sequence[LSTMTrial] | None = None, seed: int = 42,
) -> tuple[dict, dict[tuple[date, str], float]]:
    config.validate()
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
    device = torch.device('cuda:0' if gpu_count else 'cpu')

    class Network(nn.Module):
        def __init__(self, features: int, hidden: int):
            super().__init__()
            self.lstm = nn.LSTM(features, hidden, batch_first=True)
            self.output = nn.Linear(hidden, 1)

        def forward(self, values):
            sequence, _ = self.lstm(values)
            return self.output(sequence[:, -1]).squeeze(-1)

    x, y = torch.from_numpy(data['x']), torch.from_numpy(data['y'])
    train_indices = torch.from_numpy(np.flatnonzero(data['train']))
    validation_indices = torch.from_numpy(np.flatnonzero(data['validation']))
    loss_function = nn.MSELoss()

    def fit(use_data_parallel: bool) -> tuple[dict, float, dict, list]:
        best_state = None
        best_validation_loss = float('inf')
        selected_trial = None
        trial_results = []
        if device.type == 'cuda':
            torch.cuda.empty_cache()
        for trial_index, trial in enumerate(trials):
            torch.manual_seed(seed)
            model = Network(x.shape[-1], trial.hidden_size).to(device)
            if use_data_parallel:
                model = nn.DataParallel(model, device_ids=[0, 1])
            optimizer = torch.optim.Adam(model.parameters(), lr=trial.learning_rate)
            for epoch in range(trial.epochs):
                model.train()
                for batch in train_indices.split(trial.batch_size):
                    inputs = x[batch]
                    if device.type == 'cuda' and not use_data_parallel:
                        inputs = inputs.to(device)
                    targets = y[batch].to(device)
                    optimizer.zero_grad()
                    loss = loss_function(model(inputs), targets)
                    if not torch.isfinite(loss):
                        raise DifferencingError(f'Non-finite training loss for {symbol}')
                    loss.backward()
                    optimizer.step()
                model.eval()
                validation_inputs = x[validation_indices]
                if device.type == 'cuda' and not use_data_parallel:
                    validation_inputs = validation_inputs.to(device)
                with torch.no_grad():
                    validation_loss = float(loss_function(
                        model(validation_inputs), y[validation_indices].to(device),
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

    used_data_parallel = False
    gpu_oom_fallback = False
    if gpu_count:
        try:
            best_model, best_loss, best_metadata, results = fit(use_data_parallel=False)
        except torch.cuda.OutOfMemoryError as exc:
            if gpu_count < 2:
                raise DifferencingError(
                    'LSTM ran out of memory on the single available GPU; '
                    'configure two visible CUDA GPUs or reduce the batch size',
                ) from exc
            gpu_oom_fallback = True
        if gpu_oom_fallback:
            # 先退出异常处理块，使异常回溯释放失败训练所持有的 GPU 张量；
            # 然后清理 CUDA 缓存，再尝试双卡数据并行回退。
            torch.cuda.empty_cache()
            try:
                best_model, best_loss, best_metadata, results = fit(use_data_parallel=True)
                used_data_parallel = True
            except torch.cuda.OutOfMemoryError as fallback_exc:
                raise DifferencingError(
                    'LSTM ran out of memory using both available GPUs; '
                    'reduce the batch size or model size',
                ) from fallback_exc
    else:
        best_model, best_loss, best_metadata, results = fit(use_data_parallel=False)

    if best_model is None or best_metadata is None:
        raise DifferencingError('No trained model selected')
    model = Network(x.shape[-1], best_metadata['hidden_size']).to(device)
    model.load_state_dict(best_model)
    model.eval()
    forecast_indices = np.flatnonzero(data['test'])
    predictions = {}
    price_errors = []
    with torch.no_grad():
        for batch in np.array_split(forecast_indices, max(1, len(forecast_indices) // 128 + 1)):
            if not len(batch):
                continue
            output = model(x[torch.from_numpy(batch)].to(device)).detach().cpu().numpy()
            differences = output * data['y_scale'] + data['y_mean']
            for index, prediction in zip(batch, differences):
                origin = int(data['origins'][index])
                log_price = invert_one_step(float(prediction), data['logs'][:origin + 1], data['weights'])
                predicted_return = exp(log_price - data['logs'][origin]) - 1
                if not np.isfinite(predicted_return):
                    raise DifferencingError(f'Invalid inverse forecast for {symbol}')
                origin_day = data['dates'][origin]
                predictions[(origin_day, symbol)] = predicted_return
                actual_return = exp(data['logs'][origin + 1] - data['logs'][origin]) - 1
                price_errors.append(abs(predicted_return - actual_return))
    metadata = {
        'instrument': symbol, 'method': method, 'order_details': order_details,
        'sample_counts': {name: int(data[name].sum()) for name in ('train', 'validation', 'test')},
        'selected_model': best_metadata, 'validation_mse_scaled': best_loss,
        'test_return_mae': float(np.mean(price_errors)) if price_errors else None,
        'trials': results, 'seed': seed,
        'training_device': str(device),
        'visible_gpu_count': gpu_count,
        'gpu_names': [torch.cuda.get_device_name(index) for index in range(gpu_count)],
        'data_parallel_gpus': [0, 1] if used_data_parallel else [],
        'gpu_oom_fallback': gpu_oom_fallback,
        'model': {name: tensor.tolist() for name, tensor in best_model.items()},
        'scaler': {
            'x_mean': data['x_mean'].tolist(), 'x_scale': data['x_scale'].tolist(),
            'y_mean': data['y_mean'], 'y_scale': data['y_scale'],
        },
        'weights': data['weights'].tolist(),
        'config': {name: value.isoformat() if isinstance(value, date) else value
                   for name, value in asdict(config).items()},
    }
    return metadata, predictions
