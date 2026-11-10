# coding:utf-8
"""Backtest-only fractional-difference ETF strategy for QMT's Python editor.

The strategy uses QMT's ContextInfo and order_shares APIs. It does not connect
to miniQMT and refuses to run outside QMT backtest mode.

V2 evaluates risks daily, ordinary targets every five trading bars. Equity
stress blocks equity ETFs, not independently screened defensive assets.
Portfolio drawdown instead suspends all assets. Global peak is never reset;
the separate episode reference resets only after a completed risk cooldown.
Match the QMT fee panel to the cost constants below. Historical distributions,
tradability and fund inception must be verified in the QMT report.

Research inspiration (not reproductions or performance guarantees):
https://arxiv.org/abs/2611.05310 -- persistent regimes and turnover control.
https://arxiv.org/abs/2611.04826 -- abstention from unsupported predictions.
Historical money-flow fields are not wired until their API and timestamps
are confirmed; live flow must never enter historical features.

V5 adds an optional fractional-feature LSTM. The active experiment uses
MODEL_TYPE='fractional' and FRACTIONAL_HISTORY_COUNT=504 as a window-matched
regression control against the prior LSTM run. Keep the same pool, fees and
dates when comparing them. LSTM needs 504 bars; newly listed ETFs
are excluded until sufficient real history exists. Training, early-stopping
selection and the final signal gate use separate chronological subsets.
These constants belong here, not in QMT's CCI template parameter panel.
QMT never imports torch: two persistent isolated Python processes handle
independent ETF fits on CUDA 0/1, reusing runtimes, not trained models.
Set LSTM_DUAL_GPU=False for one GPU; missing requested hardware is an error.
It exits after 120 idle seconds or when its parent closes. Keep this source
file on disk at LSTM_WORKER_SCRIPT when pasting it into QMT. The worker reads
no accounts and submits no orders. Training is still causal at each rebalance;
runtime acceleration does not make this backtest-only script live-trade ready.
Execution opens are read from timestamped unadjusted daily bars for exactly
the simulated date, with no suspension filling or live subscriptions. Signal
history remains unchanged. Run QMT on a daily main chart without adjustment;
otherwise the simulator may match against a different price basis.
Missing held bars trigger a read-only 20-bar diagnostic from the same broker
API, ending on the simulated date. Diagnostic prices never become orders.
Verified full-day suspensions retain shares and reserve exposure using the
last completed raw close, solely for sizing (not fills or account valuation).
Unknown missing held bars still stop orders. Suspended shares cannot be sold
even during portfolio risk-off; the exposure limit is not a liquidation guarantee.

Execution-control experiment: retain deliberately skipped sub-threshold
reductions in the effective share targets, so they do not block unrelated buys.
Submitted reductions must still be confirmed before buying; retained and
suspended exposure still consumes the original 60% portfolio limit.
Signals, risk thresholds, fees and model settings are unchanged for comparison.

Risk-recovery experiment: shorten only the equity-stress cooldown to five
trading bars. Portfolio drawdown keeps its 20-bar cooldown, and equity entries
still require benchmark recovery with no active stress.
"""

from math import isfinite, sqrt

import numpy as np


EQUITY_ETFS = (
    '510300.SH',  # CSI 300
    '510500.SH',  # CSI 500
    '159915.SZ',  # ChiNext
    '588000.SH',  # STAR 50
    '510050.SH',  # SSE 50
    '510880.SH',  # SSE dividend
    '512890.SH',  # CSI dividend low volatility
)
DEFENSIVE_ETFS = (
    '511010.SH',  # Treasury bonds
    '518880.SH',  # Gold
    '511880.SH',  # Money market
)
ETF_UNIVERSE = EQUITY_ETFS + DEFENSIVE_ETFS

HISTORY_COUNT = 122
REBALANCE_INTERVAL = 5
MAX_HOLDINGS = 3
MAX_TOTAL_EXPOSURE = 0.60
MAX_SINGLE_WEIGHT = 0.30
MIN_TRADE_WEIGHT = 0.03
MAX_PEAK_DRAWDOWN = 0.06
STRESS_DAILY_RETURN = -0.05
STRESS_FIVE_DAY_RETURN = -0.08
STRESS_ANNUAL_VOLATILITY = 0.40
RISK_OFF_COOLDOWN = 20
EQUITY_RISK_OFF_COOLDOWN = 5
LOT_SIZE = 100
CASH_RESERVE_RATE = 0.005
BACKTEST_ACCOUNT = 'testS'
DIFFERENCE_ORDER = 0.5
DIFFERENCE_THRESHOLD = 0.001
PREDICTION_LAGS = 5
FORECAST_HORIZON = 5
COMMISSION_RATE = 0.00015
SLIPPAGE_RATE = 0.0005
MIN_COMMISSION = 5.0
RANK_RETENTION_BONUS = 0.10
MIN_PREDICTED_RETURN = 2 * (COMMISSION_RATE + SLIPPAGE_RATE)
MODEL_TYPE = 'fractional'
LSTM_DEVICE = 'cuda'
FRACTIONAL_HISTORY_COUNT = 504
LSTM_HISTORY_COUNT = 504
LSTM_SEQUENCE_LENGTH = 20
LSTM_HIDDEN_SIZE = 32
LSTM_LAYERS = 1
LSTM_EPOCHS = 30
LSTM_BATCH_SIZE = 128
LSTM_LEARNING_RATE = 0.001
LSTM_PATIENCE = 5
LSTM_SEED = 42
LSTM_WORKER_PYTHON = (
    'E:\\\u4e2d\u6cf0\u8bc1\u5238QMT\u4fe1\u521b\u5b9e\u76d8'
    '\\bin.x64\\python312\\python.exe'
)
LSTM_WORKER_SCRIPT = (
    'E:\\\u91cf\u5316\\stock\\backend\\strategies\\qmt_etf_rotation.py'
)
LSTM_WORKER_TIMEOUT = 180
LSTM_PERSISTENT_WORKER = True
LSTM_DUAL_GPU = True
LSTM_WORKER_SETTINGS = (
    'LSTM_DEVICE', 'LSTM_HISTORY_COUNT', 'LSTM_SEQUENCE_LENGTH',
    'LSTM_HIDDEN_SIZE', 'LSTM_LAYERS', 'LSTM_EPOCHS', 'LSTM_BATCH_SIZE',
    'LSTM_LEARNING_RATE', 'LSTM_PATIENCE', 'LSTM_SEED',
    'DIFFERENCE_ORDER', 'DIFFERENCE_THRESHOLD', 'FORECAST_HORIZON',
)
_lstm_clients = {}
# Full-day suspension announced on the same day, not inferred from missing data.
# https://vip.stock.finance.sina.com.cn/fund/go.php/vAkFundInfo_JJGKXX/q/2219035.phtml
VERIFIED_SUSPENSIONS = {'159915.SZ': frozenset(('20210208',))}


class _LstmWorkerClient:
    """Own one child and a bounded response wait; no networking or torch in QMT."""

    def __init__(self, command, env, cwd):
        import atexit
        import queue
        import subprocess
        import threading
        from collections import deque

        self.responses = queue.Queue()
        self.errors = deque(maxlen=6000)
        self.process = subprocess.Popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace',
            env=env, cwd=cwd,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.error_reader = threading.Thread(target=self._read_errors, daemon=True)
        self.reader.start()
        self.error_reader.start()
        atexit.register(self.close)

    def _read_errors(self):
        while True:
            character = self.process.stderr.read(1)
            if not character:
                return
            self.errors.append(character)

    def _read(self):
        try:
            for line in self.process.stdout:
                self.responses.put(line)
        finally:
            self.responses.put(None)

    def request(self, payload):
        import queue

        try:
            self.process.stdin.write(payload + '\n')
            self.process.stdin.flush()
        except (OSError, ValueError) as exc:
            raise RuntimeError('LSTM worker input failed: ' + str(exc)) from exc
        try:
            response = self.responses.get(timeout=LSTM_WORKER_TIMEOUT)
        except queue.Empty as exc:
            raise RuntimeError('LSTM worker response timed out') from exc
        if response is None:
            self.process.wait(timeout=5)
            self.error_reader.join(timeout=5)
            raise RuntimeError('LSTM worker exited:\n' + ''.join(self.errors))
        return response

    def close(self):
        import atexit

        if self.process.poll() is None:
            self.process.kill()
        self.process.wait()
        self.reader.join(timeout=5)
        self.error_reader.join(timeout=5)
        self.process.stdin.close()
        self.process.stdout.close()
        self.process.stderr.close()
        atexit.unregister(self.close)


def close_lstm_worker(device=None):
    devices = list(_lstm_clients) if device is None else [device]
    for name in devices:
        client = _lstm_clients.pop(name, None)
        if client is not None:
            client.close()


def isolated_lstm_batch(histories):
    """Split independent ETF fits across two persistent CUDA workers."""
    if LSTM_DUAL_GPU and LSTM_DEVICE == 'cuda':
        from concurrent.futures import ThreadPoolExecutor

        items = list(histories.items())
        groups = [dict(items[::2]), dict(items[1::2])]
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(_isolated_lstm_batch, group, 'cuda:' + str(index))
                           for index, group in enumerate(groups)]
                results = [future.result() for future in futures]
        except RuntimeError:
            close_lstm_worker()
            raise
        return {'device': 'cuda', 'forecasts': {
            symbol: forecast for result in results
            for symbol, forecast in result['forecasts'].items()}}
    return _isolated_lstm_batch(histories, LSTM_DEVICE)


def _isolated_lstm_batch(histories, device):
    """Exchange only historical prices and settings with a bounded GPU worker."""
    import json
    import os
    import subprocess

    for path in (LSTM_WORKER_PYTHON, LSTM_WORKER_SCRIPT):
        if not os.path.isfile(path):
            raise RuntimeError('LSTM worker file unavailable: ' + path)
    payload = {
        'settings': {name: globals()[name] for name in LSTM_WORKER_SETTINGS},
        'histories': histories,
    }
    payload['settings']['LSTM_DEVICE'] = device
    env = os.environ.copy()
    for name in ('PYTHONHOME', 'PYTHONPATH'):
        env.pop(name, None)
    command = [LSTM_WORKER_PYTHON, '-I', LSTM_WORKER_SCRIPT]
    serialized = json.dumps(payload, allow_nan=False)
    try:
        if LSTM_PERSISTENT_WORKER:
            client = _lstm_clients.get(device)
            if client is not None and client.process.poll() is not None:
                code = client.process.returncode
                close_lstm_worker(device)
                if code != 0:
                    raise RuntimeError('LSTM worker exited unexpectedly with code ' + str(code))
                client = None
            if client is None:
                client = _LstmWorkerClient(
                    command + ['--lstm-worker-stream'], env, os.path.dirname(LSTM_WORKER_PYTHON))
                _lstm_clients[device] = client
            response = client.request(serialized)
        else:
            completed = subprocess.run(
                command + ['--lstm-worker'],
                input=serialized, capture_output=True,
                text=True, encoding='utf-8', env=env, cwd=os.path.dirname(LSTM_WORKER_PYTHON),
                timeout=LSTM_WORKER_TIMEOUT,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
            )
            if completed.returncode != 0:
                raise RuntimeError('LSTM worker failed:\n'
                                   + completed.stderr[-6000:] + completed.stdout[-2000:])
            response = completed.stdout
    except (OSError, subprocess.TimeoutExpired, RuntimeError) as exc:
        close_lstm_worker(device)
        raise RuntimeError('Isolated LSTM worker failed; no orders submitted: ' + str(exc)) from exc
    try:
        result = json.loads(response)
    except json.JSONDecodeError as exc:
        close_lstm_worker(device)
        raise RuntimeError('Invalid LSTM worker response: ' + response[-2000:]) from exc
    if (not isinstance(result, dict) or not isinstance(result.get('forecasts'), dict)
            or set(result['forecasts']) != set(histories)
            or result.get('device') != device):
        close_lstm_worker(device)
        raise RuntimeError('LSTM worker response has incompatible symbols or device')
    for forecast in result['forecasts'].values():
        if (not isinstance(forecast, dict)
                or type(forecast.get('validation_passed')) is not bool
                or any(type(forecast.get(key)) not in (int, float)
                       or not isfinite(forecast[key]) for key in (
                           'predicted_return', 'validation_mse', 'baseline_mse'))
                or forecast['validation_mse'] < 0 or forecast['baseline_mse'] < 0
                or forecast['validation_passed'] != (
                    forecast['validation_mse'] < forecast['baseline_mse'])):
            close_lstm_worker(device)
            raise RuntimeError('Invalid LSTM worker forecast')
    return result


def forecast_history_count():
    if MODEL_TYPE not in ('fractional', 'lstm'):
        raise ValueError('MODEL_TYPE must be fractional or lstm')
    count = LSTM_HISTORY_COUNT if MODEL_TYPE == 'lstm' else FRACTIONAL_HISTORY_COUNT
    if isinstance(count, bool) or not isinstance(count, int) or count < HISTORY_COUNT:
        raise ValueError('Forecast history count must be an integer >= HISTORY_COUNT')
    return count


def fractional_weights(order=DIFFERENCE_ORDER, threshold=DIFFERENCE_THRESHOLD,
                       max_lags=1000):
    """Standalone equivalent of research.fractional_forecast's recurrence."""
    if (not isfinite(order) or not 0 <= order <= 1
            or not isfinite(threshold) or not 0 < threshold < 1
            or isinstance(max_lags, bool) or not isinstance(max_lags, int)
            or max_lags < 2):
        raise ValueError('Invalid fractional differencing parameters')
    weights = [1.0]
    for lag in range(1, max_lags):
        value = -weights[-1] * (order - lag + 1) / lag
        if abs(value) < threshold:
            return np.asarray(weights, dtype=float)
        weights.append(value)
    raise ValueError('Fractional weights did not truncate')


def difference_forecast(closes):
    """Forecast five-day log returns from causal fractional-difference features.

    Fixed order 0.5 is experimental. Purge overlapping training labels before
    chronological validation; all target prices precede the current bar.
    """
    if closes is None or len(closes) < HISTORY_COUNT:
        raise ValueError('Insufficient forecast history')
    values = np.asarray(closes[:-1], dtype=float)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError('Forecast requires finite positive completed closes')
    logs = np.log(values)
    weights = fractional_weights()
    transformed = np.convolve(logs, weights, mode='valid')
    count = len(transformed) - PREDICTION_LAGS - FORECAST_HORIZON + 1
    split = int(count * 0.75)
    train_end = split - FORECAST_HORIZON
    if train_end < 30 or count - split < 10:
        raise ValueError('Insufficient chronological training/validation samples')
    x = np.asarray([transformed[i:i + PREDICTION_LAGS]
                    for i in range(count)])
    origins = np.arange(count) + len(weights) - 1 + PREDICTION_LAGS - 1
    y = logs[origins + FORECAST_HORIZON] - logs[origins]
    mean = x[:train_end].mean(axis=0)
    scale = x[:train_end].std(axis=0)
    scale = np.maximum(scale, 1e-8)
    design = np.column_stack((np.ones(count), (x - mean) / scale))
    target_mean = float(y[:train_end].mean())
    penalty = np.eye(design.shape[1]) * 0.01
    penalty[0, 0] = 0
    coefficients = np.linalg.solve(
        design[:train_end].T @ design[:train_end] + penalty,
        design[:train_end].T @ (y[:train_end] - target_mean),
    )
    predicted = design[split:] @ coefficients + target_mean
    predicted_returns = np.expm1(predicted)
    actual_returns = np.expm1(y[split:])
    mse = float(np.mean((np.asarray(predicted_returns) - actual_returns) ** 2))
    baseline_mse = float(np.mean(np.asarray(actual_returns) ** 2))
    latest = np.r_[1.0, (transformed[-PREDICTION_LAGS:] - mean) / scale]
    predicted_return = float(np.expm1(latest @ coefficients + target_mean))
    if not all(isfinite(value) for value in (mse, baseline_mse, predicted_return)):
        raise RuntimeError('Non-finite fractional forecast')
    return {
        'predicted_return': predicted_return,
        'validation_mse': mse,
        'baseline_mse': baseline_mse,
        'validation_passed': mse < baseline_mse,
        'difference_order': DIFFERENCE_ORDER,
        'horizon': FORECAST_HORIZON,
        'training_samples': train_end,
        'validation_samples': count - split,
        'last_training_target_index': int(origins[train_end - 1] + FORECAST_HORIZON),
        'first_validation_origin_index': int(origins[split]),
    }


def lstm_dataset(closes):
    """Build causal sequences; purge five-day labels at both subset boundaries."""
    if (isinstance(LSTM_SEQUENCE_LENGTH, bool)
            or not isinstance(LSTM_SEQUENCE_LENGTH, int) or LSTM_SEQUENCE_LENGTH < 2):
        raise ValueError('LSTM sequence length must be an integer >= 2')
    if closes is None or len(closes) < LSTM_HISTORY_COUNT:
        raise ValueError('Insufficient LSTM history')
    prices = np.asarray(closes[:-1], dtype=float)
    if not np.isfinite(prices).all() or (prices <= 0).any():
        raise ValueError('LSTM requires finite positive completed closes')
    logs = np.log(prices)
    weights = fractional_weights()
    transformed = np.convolve(logs, weights, mode='valid')
    count = len(transformed) - LSTM_SEQUENCE_LENGTH - FORECAST_HORIZON + 1
    selection_start, gate_start = int(count * 0.6), int(count * 0.8)
    train_end = selection_start - FORECAST_HORIZON
    selection_end = gate_start - FORECAST_HORIZON
    if (train_end < 100 or selection_end - selection_start < 30
            or count - gate_start < 30):
        raise ValueError('Insufficient LSTM training/selection/gate samples')
    x = np.asarray([transformed[i:i + LSTM_SEQUENCE_LENGTH] for i in range(count)])
    origins = np.arange(count) + len(weights) - 1 + LSTM_SEQUENCE_LENGTH - 1
    targets = logs[origins + FORECAST_HORIZON] - logs[origins]
    mean, scale = float(x[:train_end].mean()), max(float(x[:train_end].std()), 1e-8)
    target_mean = float(targets[:train_end].mean())
    target_scale = max(float(targets[:train_end].std()), 1e-6)
    return {
        'x': ((x - mean) / scale).astype(np.float32)[..., None],
        'y': ((targets - target_mean) / target_scale).astype(np.float32),
        'latest': ((transformed[-LSTM_SEQUENCE_LENGTH:] - mean) / scale)
                  .astype(np.float32).reshape(1, LSTM_SEQUENCE_LENGTH, 1),
        'actual': np.expm1(targets),
        'origins': origins,
        'train_end': train_end, 'selection_start': selection_start,
        'selection_end': selection_end, 'gate_start': gate_start,
        'target_mean': target_mean, 'target_scale': target_scale,
    }


def lstm_device():
    import torch

    if LSTM_DEVICE not in ('cpu', 'cuda', 'cuda:0', 'cuda:1'):
        raise ValueError('LSTM_DEVICE must be cpu, cuda, cuda:0 or cuda:1')
    if LSTM_DEVICE.startswith('cuda') and not torch.cuda.is_available():
        raise RuntimeError('LSTM CUDA requested but unavailable; no CPU fallback')
    if LSTM_DEVICE == 'cuda:1' and torch.cuda.device_count() < 2:
        raise RuntimeError('Dual GPU requested but CUDA device 1 unavailable; no fallback')
    return torch.device(LSTM_DEVICE)


def lstm_forecast(closes):
    """Fit one fixed small model; gate only on data not used for early stopping."""
    import torch

    sizes = (LSTM_HIDDEN_SIZE, LSTM_LAYERS, LSTM_EPOCHS, LSTM_BATCH_SIZE, LSTM_PATIENCE)
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 1
           for value in sizes):
        raise ValueError('LSTM sizes, epochs and patience must be positive integers')
    if not isfinite(LSTM_LEARNING_RATE) or not 0 < LSTM_LEARNING_RATE < 1:
        raise ValueError('Invalid LSTM learning rate')
    data = lstm_dataset(closes)
    device = lstm_device()
    cuda_devices = ([device.index if device.index is not None else torch.cuda.current_device()]
                    if device.type == 'cuda' else [])
    # Preserve the embedding client's RNG and backend settings.
    with torch.random.fork_rng(devices=cuda_devices), torch.backends.cudnn.flags(
            benchmark=False, deterministic=True):
        torch.manual_seed(LSTM_SEED)
        recurrent = torch.nn.LSTM(1, LSTM_HIDDEN_SIZE, num_layers=LSTM_LAYERS,
                                  batch_first=True).to(device)
        head = torch.nn.Linear(LSTM_HIDDEN_SIZE, 1).to(device)
        parameters = list(recurrent.parameters()) + list(head.parameters())
        optimizer = torch.optim.Adam(parameters, lr=LSTM_LEARNING_RATE)
        x = torch.as_tensor(data['x'], device=device)
        y = torch.as_tensor(data['y'], device=device)

        def predict(inputs):
            sequence, _ = recurrent(inputs)
            return head(sequence[:, -1]).squeeze(-1)

        best_loss, checkpoint, wait, best_epoch = float('inf'), None, 0, 0
        for epoch in range(1, LSTM_EPOCHS + 1):
            recurrent.train()
            head.train()
            for start in range(0, data['train_end'], LSTM_BATCH_SIZE):
                end = min(start + LSTM_BATCH_SIZE, data['train_end'])
                optimizer.zero_grad()
                loss = torch.nn.functional.mse_loss(predict(x[start:end]), y[start:end])
                if not torch.isfinite(loss).item():
                    raise RuntimeError('Non-finite LSTM training loss')
                loss.backward()
                torch.nn.utils.clip_grad_norm_(parameters, 1.0, error_if_nonfinite=True)
                optimizer.step()
            recurrent.eval()
            head.eval()
            with torch.no_grad():
                selection = slice(data['selection_start'], data['selection_end'])
                selection_loss = torch.nn.functional.mse_loss(
                    predict(x[selection]), y[selection]).item()
            if not isfinite(selection_loss):
                raise RuntimeError('Non-finite LSTM selection loss')
            if selection_loss < best_loss - 1e-6:
                best_loss, wait, best_epoch = selection_loss, 0, epoch
                checkpoint = (
                    {k: v.detach().clone() for k, v in recurrent.state_dict().items()},
                    {k: v.detach().clone() for k, v in head.state_dict().items()},
                )
            else:
                wait += 1
                if wait >= LSTM_PATIENCE:
                    break
        if checkpoint is None:
            raise RuntimeError('LSTM did not produce a checkpoint')
        recurrent.load_state_dict(checkpoint[0])
        head.load_state_dict(checkpoint[1])
        with torch.no_grad():
            gate_outputs = predict(x[data['gate_start']:]).cpu().numpy()
            latest_output = predict(torch.as_tensor(data['latest'], device=device)).item()
    predicted = np.expm1(gate_outputs * data['target_scale'] + data['target_mean'])
    actual = data['actual'][data['gate_start']:]
    mse, baseline = float(np.mean((predicted - actual) ** 2)), float(np.mean(actual ** 2))
    predicted_return = float(np.expm1(
        latest_output * data['target_scale'] + data['target_mean']))
    if not all(isfinite(value) for value in (mse, baseline, predicted_return)):
        raise RuntimeError('Non-finite LSTM forecast')
    return {
        'model': 'fractional_lstm', 'device': str(device), 'best_epoch': best_epoch,
        'predicted_return': predicted_return, 'validation_mse': mse,
        'baseline_mse': baseline, 'validation_passed': mse < baseline,
        'difference_order': DIFFERENCE_ORDER, 'horizon': FORECAST_HORIZON,
        'training_samples': data['train_end'],
        'selection_samples': data['selection_end'] - data['selection_start'],
        'validation_samples': len(actual),
    }


def _finite_positive(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not isfinite(number) or number <= 0:
        return None
    return number


def score_history(closes, symbol=None, round_trip_cost=MIN_PREDICTED_RETURN,
                  forecast=None):
    """Use forecasts for risky assets and a cost-gated trend for bonds/cash ETFs."""
    required = HISTORY_COUNT if symbol in ('511010.SH', '511880.SH') else forecast_history_count()
    if closes is None or len(closes) < required:
        return None
    prices = [_finite_positive(value) for value in closes]
    if any(value is None for value in prices):
        return None

    signal_close = prices[-2]
    momentum_20 = signal_close / prices[-22] - 1
    momentum_60 = signal_close / prices[-62] - 1
    recent_prices = prices[-22:-1]
    returns = [right / left - 1 for left, right in zip(recent_prices, recent_prices[1:])]
    if len(returns) != 20:
        return None
    average_return = sum(returns) / len(returns)
    variance = sum((value - average_return) ** 2 for value in returns) / len(returns)
    annual_volatility = sqrt(variance * 252)

    if symbol in ('511010.SH', '511880.SH'):
        trend_average = sum(prices[-61:-1]) / 60
        if signal_close <= trend_average or momentum_60 <= 2 * round_trip_cost:
            return None
        return {
            'score': (momentum_60 - 2 * round_trip_cost) / max(annual_volatility, 0.03),
            'momentum_20': momentum_20,
            'momentum_60': momentum_60,
            'annual_volatility': annual_volatility,
            'signal': 'defensive_60_day_trend_not_return_forecast',
            'estimated_round_trip_cost': round_trip_cost,
        }

    if forecast is None:
        forecast = (isolated_lstm_batch({'single': prices})['forecasts']['single']
                    if MODEL_TYPE == 'lstm' else difference_forecast(prices))
    if (not forecast['validation_passed']
            or forecast['predicted_return'] <= round_trip_cost):
        return None
    score = (forecast['predicted_return'] - round_trip_cost) / max(annual_volatility, 0.03)
    return {
        'score': score,
        'momentum_20': momentum_20,
        'momentum_60': momentum_60,
        'annual_volatility': annual_volatility,
        'forecast': forecast,
        'estimated_round_trip_cost': round_trip_cost,
    }


def analyze_benchmark(closes):
    """Detect broad-market stress and recovery from completed daily bars."""
    if closes is None or len(closes) < HISTORY_COUNT:
        return None
    prices = [_finite_positive(value) for value in closes]
    if any(value is None for value in prices):
        return None

    signal_close = prices[-2]
    prior_close = prices[-3]
    trend_average = sum(prices[-121:-1]) / 120
    momentum_20 = signal_close / prices[-22] - 1
    daily_return = signal_close / prior_close - 1
    five_day_return = signal_close / prices[-7] - 1
    recent_prices = prices[-22:-1]
    returns = [right / left - 1 for left, right in zip(recent_prices, recent_prices[1:])]
    average_return = sum(returns) / len(returns)
    variance = sum((value - average_return) ** 2 for value in returns) / len(returns)
    annual_volatility = sqrt(variance * 252)

    reasons = []
    if daily_return <= STRESS_DAILY_RETURN:
        reasons.append('benchmark_daily_shock')
    if five_day_return <= STRESS_FIVE_DAY_RETURN:
        reasons.append('benchmark_five_day_drawdown')
    if annual_volatility >= STRESS_ANNUAL_VOLATILITY:
        reasons.append('benchmark_volatility_spike')
    if signal_close < trend_average and momentum_20 <= -0.02:
        reasons.append('benchmark_bear_trend')
    return {
        'stress': bool(reasons),
        'reason': ','.join(reasons),
        'recovered': signal_close > trend_average and momentum_20 > 0,
        'daily_return': daily_return,
        'five_day_return': five_day_return,
        'annual_volatility': annual_volatility,
    }


def build_targets(histories, held=(), equity_blocked=False, balance=None):
    """Return fixed-pool allocations filtered by validated fractional forecasts."""
    if not histories:
        raise ValueError('ETF histories are empty')
    features = {}
    rejected = {}
    forecasts = {}
    if MODEL_TYPE == 'lstm':
        eligible = {
            symbol: [float(value) for value in histories[symbol]]
            for symbol in ETF_UNIVERSE
            if symbol not in ('511010.SH', '511880.SH')
            and not (equity_blocked and symbol in EQUITY_ETFS)
            and symbol in histories and len(histories[symbol]) >= forecast_history_count()
            and all(_finite_positive(value) is not None for value in histories[symbol])
        }
        if eligible:
            from time import perf_counter

            started = perf_counter()
            forecasts = isolated_lstm_batch(eligible)['forecasts']
            print('LSTM batch:', len(eligible), 'ETFs; elapsed seconds:',
                  round(perf_counter() - started, 3))
    for symbol in ETF_UNIVERSE:
        if equity_blocked and symbol in EQUITY_ETFS:
            rejected[symbol] = 'equity_risk_off'
            continue
        cost = MIN_PREDICTED_RETURN
        if balance is not None:
            budget = balance * MAX_TOTAL_EXPOSURE / MAX_HOLDINGS
            cost = 2 * (max(COMMISSION_RATE, MIN_COMMISSION / budget) + SLIPPAGE_RATE)
        if symbol in forecasts:
            result = score_history(histories.get(symbol), symbol, cost, forecasts[symbol])
        else:
            result = score_history(histories.get(symbol), symbol, cost)
        if result is None:
            rejected[symbol] = 'invalid_history_or_forecast_validation_or_return_filter'
        else:
            features[symbol] = result

    selected = sorted(features, key=lambda symbol: (
        -features[symbol]['score'] * (1 + RANK_RETENTION_BONUS if symbol in held else 1),
        symbol,
    ))
    selected = selected[:MAX_HOLDINGS]
    weights = {symbol: 0.0 for symbol in ETF_UNIVERSE}
    if selected:
        exposure = min(MAX_TOTAL_EXPOSURE, MAX_SINGLE_WEIGHT * len(selected))
        weight = exposure / len(selected)
        for symbol in selected:
            weights[symbol] = weight
    return {
        'selected': selected,
        'weights': weights,
        'cash_weight': 1 - sum(weights.values()),
        'features': features,
        'rejected': rejected,
    }


def _require_backtest(ContextInfo):
    if not bool(getattr(ContextInfo, 'do_back_test', False)):
        raise RuntimeError('This strategy is backtest-only; live trading is disabled')


def init(ContextInfo):
    _require_backtest(ContextInfo)
    close_lstm_worker()
    forecast_history_count()
    if MODEL_TYPE == 'lstm':
        device = isolated_lstm_batch({})['device']
        print('LSTM device:', device, 'history:', LSTM_HISTORY_COUNT,
              'sequence:', LSTM_SEQUENCE_LENGTH, 'hidden:', LSTM_HIDDEN_SIZE,
              'layers:', LSTM_LAYERS, 'epochs:', LSTM_EPOCHS,
              'batch:', LSTM_BATCH_SIZE, 'learning_rate:', LSTM_LEARNING_RATE,
              'patience:', LSTM_PATIENCE, 'seed:', LSTM_SEED)
        print('LSTM persistent workers:', LSTM_PERSISTENT_WORKER,
              'dual GPU:', LSTM_DUAL_GPU)
    ContextInfo.set_universe(list(ETF_UNIVERSE))
    ContextInfo.accountID = BACKTEST_ACCOUNT
    ContextInfo.rotation_last_bar = -1
    ContextInfo.risk_off_until = -1
    ContextInfo.portfolio_off_until = -1
    ContextInfo.peak_balance = float(ContextInfo.capital)
    ContextInfo.risk_reference_balance = ContextInfo.peak_balance
    ContextInfo.benchmark = '510300.SH'
    print('QMT internal backtest only; miniQMT connection is not used.')
    print('QMT percentage fee panel: ETF buy/sell commission 0.015%, not 0.00015%.')
    print('Set ETF stamp duty to 0; confirm minimum commission and slippage with your broker.')
    print('Risk triggers: benchmark daily -5%, 5-day -8%, volatility 40%, portfolio drawdown 6%.')
    print('Risk cooldowns: equity stress:', EQUITY_RISK_OFF_COOLDOWN,
          'bars; portfolio drawdown:', RISK_OFF_COOLDOWN, 'bars.')
    print('EXPERIMENT: 5-bar equity-stress cooldown; recovery confirmation unchanged.')
    print('Risk triggers are not hard loss limits and cannot guarantee returns.')
    print('Signal model:', MODEL_TYPE, 'fractional features, 5-day return, purged validation.')
    if MODEL_TYPE == 'fractional':
        print('EXPERIMENT: 504-bar fractional Ridge control; match dates, ETF pool, fees, and risk settings to the LSTM run.')
    print('Weekly rebalance; daily equity risk checks; bonds/cash use cost-gated 60-day trend.')
    print('Cost assumptions: commission 0.015%, slippage 0.05%, minimum commission 5 CNY.')
    print('Execution: exact-date raw open; use a 1d unadjusted QMT main chart.')
    print('PRICE_DIAGNOSTICS_V2: raw versus follow price check enabled.',
          'Context dividend_type:', getattr(ContextInfo, 'dividend_type', 'unavailable'))
    print('ETF pool:', ETF_UNIVERSE, 'No leverage; maximum total exposure:', MAX_TOTAL_EXPOSURE)


def _account_snapshot(ContextInfo):
    accounts = get_trade_detail_data(ContextInfo.accountID, 'STOCK', 'ACCOUNT')
    if not accounts:
        raise RuntimeError('QMT backtest returned no account data')
    account = accounts[0]
    try:
        balance = float(account.m_dBalance)
        available = float(account.m_dAvailable)
    except (AttributeError, TypeError, ValueError) as exc:
        raise RuntimeError('QMT account data lacks balance or available cash') from exc
    if not isfinite(balance) or balance <= 0 or not isfinite(available) or available < 0:
        raise RuntimeError('QMT backtest returned invalid balance or available cash')
    return balance, available


def _positions(ContextInfo):
    result = {}
    for position in get_trade_detail_data(ContextInfo.accountID, 'STOCK', 'POSITION'):
        symbol = position.m_strInstrumentID + '.' + position.m_strExchangeID
        volume = int(position.m_nVolume or 0)
        if volume > 0:
            result[symbol] = volume
    unexpected = sorted(set(result) - set(ETF_UNIVERSE))
    if unexpected:
        raise RuntimeError('Backtest account contains positions outside this strategy universe: '
                           + ', '.join(unexpected))
    return result


def _submit(ContextInfo, symbol, shares, price):
    result = order_shares(
        symbol, shares, 'fix', price, ContextInfo, ContextInfo.accountID,
    )
    if isinstance(result, (int, float)) and result < 0:
        raise RuntimeError('QMT rejected {} order for {} shares'.format(symbol, shares))


def _execute_targets(ContextInfo, targets, positions, execution_prices, balance,
                     frozen_prices=None):
    frozen_prices = frozen_prices or {}
    target_shares = {}
    for symbol in ETF_UNIVERSE:
        price = execution_prices.get(symbol)
        if price is None:
            continue
        value = balance * targets['weights'][symbol]
        target_shares[symbol] = int(value / price / LOT_SIZE) * LOT_SIZE

    for symbol in ETF_UNIVERSE:
        price = execution_prices.get(symbol)
        if price is None:
            continue
        current = positions.get(symbol, 0)
        target = target_shares.get(symbol, 0)
        shares_to_sell = max(0, current - target)
        if shares_to_sell <= 0:
            continue
        if target > 0 and shares_to_sell * price < balance * MIN_TRADE_WEIGHT:
            target_shares[symbol] = current
            print('Retain sub-threshold reduction:', symbol,
                  'retained_shares:', shares_to_sell,
                  'retained_value:', shares_to_sell * price)
            continue
        _submit(ContextInfo, symbol, -shares_to_sell, price)

    _, available_cash = _account_snapshot(ContextInfo)
    confirmed_positions = _positions(ContextInfo)
    for symbol, shares in confirmed_positions.items():
        if symbol in frozen_prices:
            if shares != positions.get(symbol, 0):
                raise RuntimeError('Suspended position changed unexpectedly: ' + symbol)
            continue
        if shares > target_shares.get(symbol, 0):
            print('Pending reductions; defer buys:', symbol)
            return
    positions = confirmed_positions
    valuation_prices = dict(frozen_prices)
    valuation_prices.update(execution_prices)
    if set(positions) - set(valuation_prices):
        raise RuntimeError('Confirmed position lacks exposure valuation; defer buys')
    exposure_room = max(0.0, balance * MAX_TOTAL_EXPOSURE - sum(
        shares * valuation_prices[symbol] for symbol, shares in positions.items()
    ))
    for symbol in targets['selected']:
        price = execution_prices.get(symbol)
        if price is None:
            continue
        current = positions.get(symbol, 0)
        target = target_shares.get(symbol, 0)
        shares_to_buy = max(0, target - current)
        if shares_to_buy <= 0 or shares_to_buy * price < balance * MIN_TRADE_WEIGHT:
            continue
        affordable = int(
            min(available_cash / (1 + CASH_RESERVE_RATE), exposure_room)
            / (price * LOT_SIZE)
        ) * LOT_SIZE
        shares_to_buy = min(shares_to_buy, affordable)
        if shares_to_buy <= 0:
            print('Insufficient available cash for', symbol)
            continue
        _submit(ContextInfo, symbol, shares_to_buy, price)
        available_cash -= shares_to_buy * price * (1 + CASH_RESERVE_RATE)
        exposure_room -= shares_to_buy * price


def handlebar(ContextInfo):
    _require_backtest(ContextInfo)
    bar = int(ContextInfo.barpos)
    if bar < HISTORY_COUNT:
        return

    close_data = ContextInfo.get_history_data(forecast_history_count(), '1d', 'close')
    execution_prices = execution_open_prices(ContextInfo)
    histories = {}
    for symbol in ETF_UNIVERSE:
        closes = close_data.get(symbol, [])
        if len(closes) < HISTORY_COUNT:
            continue
        histories[symbol] = closes

    benchmark = analyze_benchmark(histories.get('510300.SH'))
    if benchmark is None:
        raise RuntimeError('Benchmark history unavailable; no orders submitted')
    positions = _positions(ContextInfo)
    frozen_prices = {}
    missing_held = sorted(set(positions) - set(execution_prices))
    if missing_held:
        from datetime import datetime, timedelta, timezone

        date = datetime.fromtimestamp(
            ContextInfo.get_bar_timetag(bar) / 1000,
            timezone(timedelta(hours=8))).strftime('%Y%m%d')
        reports = audit_missing_bars(ContextInfo, missing_held, date)
        frozen_prices = suspension_valuation(positions, reports, date)
    if not histories:
        raise RuntimeError('No ETF history available; no orders submitted')

    balance, _ = _account_snapshot(ContextInfo)
    if balance > ContextInfo.peak_balance:
        ContextInfo.peak_balance = balance
    drawdown = (ContextInfo.peak_balance - balance) / ContextInfo.peak_balance
    ContextInfo.risk_reference_balance = max(ContextInfo.risk_reference_balance, balance)
    episode_drawdown = 1 - balance / ContextInfo.risk_reference_balance
    if episode_drawdown >= MAX_PEAK_DRAWDOWN and ContextInfo.portfolio_off_until < 0:
        ContextInfo.portfolio_off_until = bar + RISK_OFF_COOLDOWN
        print('PORTFOLIO_RISK_OFF:', 'episode_drawdown:', episode_drawdown,
              'global_drawdown:', drawdown)

    if benchmark['stress'] and ContextInfo.risk_off_until < 0:
        ContextInfo.risk_off_until = bar + EQUITY_RISK_OFF_COOLDOWN
        print('EQUITY_RISK_OFF:', benchmark['reason'], 'drawdown:', drawdown)

    if (ContextInfo.portfolio_off_until >= 0
            and bar > ContextInfo.portfolio_off_until and not benchmark['stress']):
        ContextInfo.portfolio_off_until = -1
        ContextInfo.risk_reference_balance = balance
        ContextInfo.rotation_last_bar = -1
    if (ContextInfo.risk_off_until >= 0
            and bar > ContextInfo.risk_off_until and benchmark['recovered']
            and not benchmark['stress']):
        ContextInfo.risk_off_until = -1
        ContextInfo.rotation_last_bar = -1

    if ContextInfo.portfolio_off_until >= 0:
        targets = {
            'selected': [],
            'weights': {symbol: 0.0 for symbol in ETF_UNIVERSE},
            'cash_weight': 1.0,
        }
        targets = reserve_suspended_targets(targets, positions, frozen_prices, balance)
        print('PORTFOLIO_RISK_OFF_HOLD:', 'global_drawdown:', drawdown,
              'cannot_liquidate_suspended:', sorted(frozen_prices))
        _execute_targets(ContextInfo, targets, positions, execution_prices, balance, frozen_prices)
        ContextInfo.rotation_last_bar = bar
        return

    equity_blocked = ContextInfo.risk_off_until >= 0
    force_equity_exit = equity_blocked and any(symbol in EQUITY_ETFS for symbol in positions)
    if (not force_equity_exit and ContextInfo.rotation_last_bar >= 0
            and bar - ContextInfo.rotation_last_bar < REBALANCE_INTERVAL):
        return

    tradable_histories = {symbol: values for symbol, values in histories.items()
                          if symbol in execution_prices}
    targets = build_targets(tradable_histories, positions, equity_blocked, balance)
    targets = reserve_suspended_targets(targets, positions, frozen_prices, balance)
    print('ETF rebalance bar:', bar, 'selected:', targets['selected'])
    print('Target weights:', targets['weights'], 'cash:', targets['cash_weight'])
    print('Forecast features:', targets['features'], 'excluded:', targets['rejected'])
    _execute_targets(ContextInfo, targets, positions, execution_prices, balance, frozen_prices)
    ContextInfo.rotation_last_bar = bar


def suspension_valuation(positions, reports, date):
    frozen = {}
    for symbol, report in reports.items():
        if date not in VERIFIED_SUSPENSIONS.get(symbol, ()):
            raise RuntimeError('Unverified missing held bar; no orders submitted: '
                               + date + ' ' + symbol)
        if any(row['date'][:8] == date for row in report['rows']):
            raise RuntimeError('Suspension conflicts with current broker bar: ' + symbol)
        prior = [row for row in report['rows'] if row['date'][:8] < date]
        if not prior:
            raise RuntimeError('Suspended holding lacks prior close valuation: ' + symbol)
        latest = max(prior, key=lambda row: row['date'])
        price = _finite_positive(latest['close'])
        if price is None:
            raise RuntimeError('Invalid suspended holding valuation: ' + symbol)
        frozen[symbol] = price
        print('SUSPENDED_POSITION_HELD:', date, symbol, 'shares:', positions[symbol],
              'sizing_only_prior_close:', price, 'close_date:', latest['date'],
              'no_order_for_this_symbol')
    return frozen


def reserve_suspended_targets(targets, positions, frozen_prices, balance):
    """Reserve frozen exposure before allocating any tradable target weights."""
    reserved = sum(positions[symbol] * price for symbol, price in frozen_prices.items()) / balance
    remaining = max(0.0, MAX_TOTAL_EXPOSURE - reserved)
    slots = max(0, MAX_HOLDINGS - len(frozen_prices))
    selected = [symbol for symbol in targets['selected']
                if symbol not in frozen_prices][:slots]
    wanted = sum(targets['weights'][symbol] for symbol in selected)
    scale = min(1.0, remaining / wanted) if wanted > 0 else 0.0
    weights = {symbol: (positions[symbol] * frozen_prices[symbol] / balance
                        if symbol in frozen_prices else weight * scale
                        if symbol in selected else 0.0)
               for symbol, weight in targets['weights'].items()}
    if reserved > MAX_TOTAL_EXPOSURE:
        print('SUSPENDED_EXPOSURE_ABOVE_LIMIT:', reserved, 'no new buys')
    return {**targets, 'weights': weights,
            'selected': [symbol for symbol in selected if weights[symbol] > 0],
            'cash_weight': 1 - sum(weights.values()),
            'frozen_sizing_weight': reserved}


def audit_missing_bars(ContextInfo, symbols, date):
    """Compare exact-day failure with an unfilled trailing query, without orders."""
    result = ContextInfo.get_market_data_ex(
        fields=['open', 'close', 'volume'], stock_code=list(symbols), period='1d',
        start_time='', end_time=date + '235959', count=20,
        dividend_type='none', fill_data=False, subscribe=False,
    )
    if not isinstance(result, dict):
        raise RuntimeError('Unexpected broker data audit response')
    reports = {}
    for symbol in symbols:
        frame = result.get(symbol)
        records = []
        if frame is not None and not frame.empty:
            if not {'open', 'close', 'volume'}.issubset(frame.columns):
                raise RuntimeError('Broker data audit missing OHLC/volume fields: ' + symbol)
            for stamp, row in frame.iterrows():
                stamp = str(stamp)
                if len(stamp) < 8 or not stamp[:8].isdigit() or stamp[:8] > date:
                    raise RuntimeError('Invalid or future-dated broker audit record: ' + stamp)
                records.append({
                    'date': stamp, 'open': float(row['open']),
                    'close': float(row['close']), 'volume': float(row['volume']),
                })
        matches = [row for row in records if row['date'][:8] == date]
        if matches:
            status = 'date_present_in_trailing_query_check_exact_day_API'
        else:
            status = 'date_absent_in_local_query_not_proof_of_source_gap_or_suspension'
        report = {'date': date, 'symbol': symbol, 'status': status,
                  'rows': records}
        reports[symbol] = report
        print('BROKER_DATA_AUDIT:', report)
    return reports


def execution_open_prices(ContextInfo):
    """Require exact-date raw opens, never use the latest available older bar."""
    from datetime import datetime, timedelta, timezone

    if getattr(ContextInfo, 'period', '1d') != '1d':
        raise RuntimeError('Execution requires a daily (1d) QMT main chart')
    timetag = ContextInfo.get_bar_timetag(ContextInfo.barpos)
    if not isinstance(timetag, (int, float)) or not isfinite(timetag) or timetag <= 0:
        raise RuntimeError('Invalid QMT bar timestamp; no orders submitted')
    date = datetime.fromtimestamp(timetag / 1000, timezone(timedelta(hours=8))).strftime('%Y%m%d')
    query = dict(
        fields=['open'], stock_code=list(ETF_UNIVERSE), period='1d',
        start_time=date, end_time=date + '235959', count=-1,
        fill_data=False, subscribe=False,
    )
    data = ContextInfo.get_market_data_ex(dividend_type='none', **query)
    chart_data = ContextInfo.get_market_data_ex(dividend_type='follow', **query)
    if not isinstance(data, dict) or not isinstance(chart_data, dict):
        raise RuntimeError('Unexpected QMT execution data response; no orders submitted')
    prices = {}
    for symbol in ETF_UNIVERSE:
        frame = data.get(symbol)
        if frame is None or frame.empty:
            print('EXECUTION_DATA_MISSING:', date, symbol, 'no current raw daily bar')
            continue
        if len(frame) != 1 or 'open' not in frame.columns:
            raise RuntimeError('Ambiguous execution daily bar: ' + date + ' ' + symbol)
        stamp = str(frame.index[0])
        if stamp[:8] != date:
            raise RuntimeError('Execution bar date mismatch: expected ' + date
                               + ', received ' + stamp + ', symbol ' + symbol)
        price = _finite_positive(frame.iloc[0]['open'])
        if price is None:
            raise RuntimeError('Invalid raw execution open: ' + date + ' ' + symbol)
        chart_frame = chart_data.get(symbol)
        if (chart_frame is None or chart_frame.empty or len(chart_frame) != 1
                or 'open' not in chart_frame.columns
                or str(chart_frame.index[0])[:8] != date):
            raise RuntimeError('Chart-basis execution bar unavailable: ' + date + ' ' + symbol)
        chart_price = _finite_positive(chart_frame.iloc[0]['open'])
        if chart_price is None:
            raise RuntimeError('Invalid chart-basis execution open: ' + date + ' ' + symbol)
        if abs(chart_price - price) > max(1e-7, price * 1e-6):
            raise RuntimeError(
                'PRICE_BASIS_MISMATCH: ' + date + ' ' + symbol
                + ' raw_open=' + str(price) + ' follow_open=' + str(chart_price)
                + ' context_dividend_type=' + str(getattr(ContextInfo, 'dividend_type', 'unavailable'))
                + '; use an unadjusted daily backtest chart; no orders submitted')
        prices[symbol] = price
    print('EXECUTION_RAW_OPEN:', date, prices)
    if date == '20170830' and '511010.SH' in prices:
        legacy = ContextInfo.get_history_data(1, '1d', 'open').get('511010.SH', [])
        print('EXECUTION_PRICE_AUDIT:', date, '511010.SH',
              'legacy_open:', list(legacy), 'dated_raw_open:', prices['511010.SH'])
    return prices


def _lstm_worker_response(payload):
    import json

    settings = payload['settings']
    if set(settings) != set(LSTM_WORKER_SETTINGS):
        raise ValueError('Incompatible worker settings; update the on-disk strategy')
    globals().update(settings)
    device = lstm_device()
    forecasts = {symbol: lstm_forecast(closes)
                 for symbol, closes in payload['histories'].items()}
    return json.dumps({'device': str(device), 'forecasts': forecasts}, allow_nan=False)


def _lstm_worker_main(stream=False):
    import json
    import queue
    import sys
    import threading

    if not stream:
        print(_lstm_worker_response(json.load(sys.stdin)))
        return
    requests = queue.Queue()

    def read_requests():
        for line in sys.stdin:
            requests.put(line)
        requests.put(None)

    threading.Thread(target=read_requests, daemon=True).start()
    while True:
        try:
            line = requests.get(timeout=120)
        except queue.Empty:
            return
        if line is None:
            return
        print(_lstm_worker_response(json.loads(line)), flush=True)


if __name__ == '__main__':
    import sys

    if sys.argv[1:] == ['--lstm-worker']:
        _lstm_worker_main()
    elif sys.argv[1:] == ['--lstm-worker-stream']:
        _lstm_worker_main(stream=True)
