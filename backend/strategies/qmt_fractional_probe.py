# coding:gbk
"""QMT init/handlebar compatibility probe; synthetic data, no trading or I/O.

Standalone by design: importing the research package would load unrelated
filesystem-dependent modules in the broker's restricted strategy environment.
The fixed differencing order is for diagnostics, not a trained strategy.
"""

import math
import sys


DEVICE = 'cpu'


def diagnostic_weights(order=0.5, threshold=0.001, max_lags=1000):
    """Match research.fractional_forecast's untempered weight recurrence."""
    if (not math.isfinite(order) or not 0 <= order <= 1
            or not math.isfinite(threshold) or not 0 < threshold < 1
            or isinstance(max_lags, bool) or not isinstance(max_lags, int)
            or max_lags < 2):
        raise ValueError('Invalid differencing settings')
    weights = [1.0]
    for lag in range(1, max_lags):
        value = -weights[-1] * (order - lag + 1) / lag
        if abs(value) < threshold:
            return weights
        weights.append(value)
    raise ValueError('Differencing weights did not truncate')


def run_probe(device_name='cpu'):
    print('QMT_PROBE_START: synthetic data only; NO ORDERS')
    print('Python:', sys.version)
    print('STAGE: import torch')
    import torch

    print('PyTorch:', torch.__version__)
    print('CUDA build:', torch.version.cuda)
    available = torch.cuda.is_available()
    print('CUDA available:', available)
    if device_name not in ('cpu', 'cuda'):
        raise ValueError('Diagnostic device must be cpu or cuda')
    if device_name == 'cuda' and not available:
        raise RuntimeError('CUDA requested but unavailable; no CPU fallback')
    device = torch.device(device_name)
    if device_name == 'cuda':
        print('GPU:', torch.cuda.get_device_name(device))
    print('Device:', device)

    print('STAGE: fractional difference')
    weights = torch.tensor(diagnostic_weights(), dtype=torch.float64, device=device)
    times = torch.arange(256, dtype=torch.float64, device=device)
    logs = math.log(10.0) + 0.001 * times + 0.02 * torch.sin(times / 7.0)
    windows = logs.unfold(0, weights.numel(), 1)
    differences = (windows.flip(1) * weights).sum(dim=1)
    sequence_length = 20
    inputs = differences[:-1].unfold(0, sequence_length, 1)
    targets = differences[sequence_length:]
    split = int(len(inputs) * 0.8)
    if split < 2 or split >= len(inputs):
        raise RuntimeError('Insufficient diagnostic sequences')
    mean = inputs[:split].mean()
    scale = inputs[:split].std()
    if not torch.isfinite(scale).item() or scale.item() <= 0:
        raise RuntimeError('Invalid diagnostic scaling')
    x = ((inputs - mean) / scale).to(torch.float32).unsqueeze(-1)
    y = ((targets - mean) / scale).to(torch.float32)

    print('STAGE: LSTM forward/backward')
    # Same LSTM + last-step linear head as fractional_lstm.build_network.
    lstm = torch.nn.LSTM(1, 16, batch_first=True).to(device)
    head = torch.nn.Linear(16, 1).to(device)
    parameters = list(lstm.parameters()) + list(head.parameters())
    optimizer = torch.optim.Adam(parameters, lr=0.001)
    optimizer.zero_grad()
    sequence, _ = lstm(x[:split])
    predictions = head(sequence[:, -1]).squeeze(-1)
    loss = torch.nn.functional.mse_loss(predictions, y[:split])
    if not torch.isfinite(loss).item():
        raise RuntimeError('Non-finite diagnostic training loss')
    loss.backward()
    if not all(p.grad is not None and torch.isfinite(p.grad).all().item()
               for p in parameters):
        raise RuntimeError('Missing or non-finite LSTM gradients')
    optimizer.step()

    print('STAGE: held-out inference and inverse difference')
    lstm.eval()
    head.eval()
    with torch.no_grad():
        sequence, _ = lstm(x[split:])
        held_out = head(sequence[:, -1]).squeeze(-1)
        validation_loss = torch.nn.functional.mse_loss(held_out, y[split:])
        latest = ((differences[-sequence_length:] - mean) / scale)
        sequence, _ = lstm(latest.to(torch.float32).reshape(1, sequence_length, 1))
        predicted_difference = head(sequence[:, -1]).reshape(()) * scale + mean
        history = logs[-(weights.numel() - 1):].flip(0)
        predicted_log = predicted_difference - (weights[1:] * history).sum()
        predicted_return = torch.expm1(predicted_log - logs[-1])
    if not (torch.isfinite(validation_loss).item()
            and torch.isfinite(predicted_return).item()):
        raise RuntimeError('Non-finite diagnostic inference')
    result = {
        'device': str(device),
        'weight_count': weights.numel(),
        'training_samples': split,
        'validation_samples': len(inputs) - split,
        'training_loss': loss.item(),
        'validation_loss': validation_loss.item(),
    }
    print('QMT_FRACTIONAL_LSTM_OK:', result)
    print('DIAGNOSTIC ONLY: one training step; NOT a trading model or signal')
    return result


def init(ContextInfo):
    run_probe(DEVICE)


def handlebar(ContextInfo):
    pass


if __name__ == '__main__':
    run_probe(DEVICE)
