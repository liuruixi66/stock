"""Benchmark identical FP32 training/validation before changing GPU settings."""

import argparse
from copy import deepcopy
from datetime import datetime
from html import escape
import json
import os
from pathlib import Path
import statistics
import subprocess
import threading
import time

import numpy as np
import torch
from torch import nn

from research.market_rotation import RotationConfig, prepare_panel
from research.rotation_training import (
    ResidentPanel, SharedLSTM, batch_loader, checked_loss, training_step,
)
from tools.run_market_rotation import save_json


def synchronize(devices):
    for index in devices:
        torch.cuda.synchronize(index)


def render_report(directory, report):
    from tools.market_rotation_dashboard import STYLE

    def average(backend, gpu):
        readings = [row[backend]['gpu_utilization'][gpu] for row in report['runs']
                    if row[backend].get('gpu_utilization')
                    and gpu in row[backend]['gpu_utilization']]
        count = sum(row['samples'] for row in readings)
        return (sum(row['mean_percent'] * row['samples'] for row in readings) / count
                if count else None)

    rows = []
    for label, key in (('训练＋验证耗时（秒）', 'seconds'),
                       ('样本吞吐（样本／秒）', 'samples_per_second')):
        values = [statistics.median(row[backend][key] for row in report['runs'])
                  for backend in ('legacy', 'resident')]
        rows.append(f'<tr><th>{label}</th><td>{values[0]:,.2f}</td><td>{values[1]:,.2f}</td></tr>')
    for gpu in ('0', '1'):
        values = [average(backend, gpu) for backend in ('legacy', 'resident')]
        rows.append(f'<tr><th>GPU {gpu} 平均利用率</th>'
                    + ''.join(f'<td>{value:.1f}%</td>' if value is not None else '<td>未采样</td>'
                              for value in values) + '</tr>')
    scope = ('完整训练集＋验证集' if report['steps_per_phase'] == 0
             else f'训练与验证各 {report["steps_per_phase"]} 批')
    html = (
        '<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>双卡训练优化实测</title><style>' + STYLE + '</style><main>'
        '<h1>双卡训练优化实测</h1><p>原始 20 轮实验完成后，使用其冻结行情进行性能对照。</p>'
        f'<section class="panel"><h2>吞吐提升 {report["speedup"]:.2f} 倍</h2>'
        f'<p>{scope}，交替顺序重复 {report["repeats"]} 次；FP32、batch 512、同样两张 GPU。</p>'
        '<table><tr><th>指标</th><th>原始路径</th><th>显存常驻批处理</th></tr>'
        + ''.join(rows) + '</table></section>'
        '<section class="panel"><h2>一致性与测量范围</h2>'
        '<p>数据切分、样本顺序、模型、优化器、batch size、梯度裁剪与数值精度不变。</p>'
        '<p>每次对照检查学习后的完整模型权重；最大绝对权重差：'
        + str(max(row['max_absolute_weight_error'] for row in report['runs']))
        + '。损失因累加顺序变化可能有微小浮点差。</p>'
        '<p>耗时含取批、传输、前后向、优化器、训练与验证；不含一次性特征处理、'
        '模型创建、首次显存装载，也不含金融回测和网页渲染。</p>'
        '<p>利用率来自 nvidia-smi 周期采样，是设备忙碌比例，不是 CUDA 核心占用率；'
        '其他共享进程、采样窗口和双卡通信均会影响数值。不保证 100% 利用率。</p>'
        '<details><summary>完整测量记录</summary><pre>'
        + escape(json.dumps(report, ensure_ascii=False, indent=2))
        + '</pre></details></section></main></html>'
    )
    (directory / 'index.html').write_text(html, encoding='utf-8')


class GPUSampler:
    def __init__(self):
        self.samples = []
        self.error = None
        self.stopped = threading.Event()
        self.thread = threading.Thread(target=self.sample, daemon=True)

    def sample(self):
        executable = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32' / 'nvidia-smi.exe'
        try:
            while not self.stopped.is_set():
                output = subprocess.run(
                    [str(executable), '--query-gpu=index,utilization.gpu',
                     '--format=csv,noheader,nounits'],
                    capture_output=True, text=True, check=True, timeout=10,
                )
                for line in output.stdout.splitlines():
                    index, utilization = map(int, line.split(','))
                    self.samples.append((index, utilization))
                self.stopped.wait(.5)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            self.error = str(exc)

    def start(self):
        self.thread.start()

    def finish(self):
        self.stopped.set()
        self.thread.join(timeout=12)
        if self.thread.is_alive() or self.error:
            raise RuntimeError(f'GPU sampler failed: {self.error}')
        return {
            str(index): {
                'mean_percent': statistics.mean(v for i, v in self.samples if i == index),
                'samples': sum(i == index for i, _ in self.samples),
            }
            for index in sorted({i for i, _ in self.samples})
        }


def measure(panel, initial, devices, batch_size, steps, backend, seed, profile_path=None,
            sample_gpu=False):
    torch.manual_seed(seed)
    device = torch.device(f'cuda:{devices[0]}')
    base = SharedLSTM().to(device)
    base.load_state_dict(initial)
    model = nn.DataParallel(base, device_ids=devices)
    optimizer = torch.optim.Adam(model.parameters(), lr=.001)
    loss_function = nn.MSELoss()
    resident = ResidentPanel(panel, 20, device) if backend == 'resident' else None
    def indices(name):
        selected = np.flatnonzero(panel['masks'][name])
        return selected[:steps * batch_size] if steps else selected

    loaders = {
        name: batch_loader(panel, indices(name),
                           20, batch_size, name == 'train', resident)
        for name in ('train', 'validation')
    }
    observed = set()
    hook = base.lstm.register_forward_hook(
        lambda module, inputs, output: observed.add(str(output[0].device)),
    )
    phases, losses = {}, {}
    profiler = (torch.profiler.profile(
        activities=[torch.profiler.ProfilerActivity.CPU, torch.profiler.ProfilerActivity.CUDA],
        record_shapes=False,
    ) if profile_path else None)
    synchronize(devices)
    if profiler:
        profiler.start()
    sampler = GPUSampler() if sample_gpu else None
    if sampler:
        sampler.start()
    for phase in ('train', 'validation'):
        model.train(phase == 'train')
        total = 0.0 if backend == 'legacy' else torch.zeros((), device=device)
        count = 0
        synchronize(devices)
        started = time.perf_counter()
        with torch.set_grad_enabled(phase == 'train'):
            for x, y, _ in loaders[phase]:
                x, y = x.to(device), y.to(device)
                if phase == 'train':
                    if backend == 'legacy':
                        optimizer.zero_grad()
                        loss = loss_function(model(x), y)
                        if not torch.isfinite(loss):
                            raise ValueError('Non-finite legacy loss')
                        loss.backward()
                        nn.utils.clip_grad_norm_(model.parameters(), 1., error_if_nonfinite=True)
                        optimizer.step()
                        loss = loss.detach()
                    else:
                        loss = training_step(model, optimizer, loss_function, x, y)
                else:
                    loss = loss_function(model(x), y)
                    if backend == 'legacy':
                        if not torch.isfinite(loss):
                            raise ValueError('Non-finite legacy validation loss')
                    else:
                        checked_loss(loss)
                if backend == 'legacy':
                    # Preserve the original loop's scalar readback overhead.
                    total += float(loss) * len(x)
                else:
                    total += loss * len(x)
                count += len(x)
                if hook is not None:
                    hook.remove()
                    hook = None
        synchronize(devices)
        phases[phase] = time.perf_counter() - started
        losses[phase] = float(total) / count
    if profiler:
        profiler.stop()
        profiler.export_chrome_trace(str(profile_path))
        profile_path.with_suffix('.txt').write_text(
            profiler.key_averages().table(sort_by='self_cpu_time_total', row_limit=25),
            encoding='utf-8',
        )
    if hook is not None:
        hook.remove()
    if observed != {f'cuda:{index}' for index in devices}:
        raise RuntimeError(f'Both GPUs did not execute: {observed}')
    return {
        'seconds': sum(phases.values()), 'phases': phases, 'losses': losses,
        'samples_per_second': sum(len(loader.dataset) for loader in loaders.values()) / sum(phases.values()),
        'observed_devices': sorted(observed),
        'gpu_utilization': sampler.finish() if sampler else None,
    }, {key: value.detach().cpu().clone() for key, value in base.state_dict().items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-directory', type=Path, required=True)
    parser.add_argument('--output-directory', type=Path, required=True)
    parser.add_argument('--steps', type=int, default=300, help='0 uses full train/validation partitions')
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--profile', action='store_true')
    parser.add_argument('--cache-directory', type=Path,
                        help='Reuse numeric cache created by a prior benchmark, not external pickle')
    parser.add_argument('--sample-gpu', action='store_true')
    args = parser.parse_args()
    if args.steps < 0 or args.repeats < 1:
        parser.error('Steps must be nonnegative and repeats must be positive')
    baseline = json.loads((args.baseline_directory / 'results.json').read_text(encoding='utf-8'))
    if baseline['status'] != 'completed':
        parser.error('Baseline experiment must be completed before optimization')
    args.output_directory.mkdir(parents=True, exist_ok=False)
    devices = [0, 1]
    if not torch.cuda.is_available() or torch.cuda.device_count() < 2:
        raise RuntimeError('Two CUDA devices required')
    torch.cuda.set_device(0)
    torch.set_num_threads(4)
    torch.manual_seed(42)
    initial = deepcopy(SharedLSTM().state_dict())
    if args.cache_directory:
        cache = args.cache_directory
        panel = {name: np.load(cache / (name + '.npy'), allow_pickle=False)
                 for name in ('features', 'ends', 'y')}
        panel['masks'] = {
            name: np.load(cache / (name + '-mask.npy'), allow_pickle=False)
            for name in ('train', 'validation', 'test')
        }
        panel.update(json.loads((cache / 'scaler.json').read_text()))
        provenance = json.loads((cache / 'provenance.json').read_text())
        if provenance['baseline'] != str(args.baseline_directory.resolve()):
            raise ValueError('Cached panel belongs to a different baseline')
    else:
        cache = args.output_directory / 'panel-cache'
        cache.mkdir()
        print('Preparing real frozen baseline panel', flush=True)
        import pandas as pd
        prices = pd.read_pickle(args.baseline_directory / 'market-snapshot.pkl')
        sessions = json.loads((args.baseline_directory / 'sessions.json').read_text())
        panel = prepare_panel(prices, sessions, RotationConfig())
        del prices
        for name in ('features', 'ends', 'y'):
            np.save(cache / (name + '.npy'), panel[name])
        for name, mask in panel['masks'].items():
            np.save(cache / (name + '-mask.npy'), mask)
        save_json(cache / 'scaler.json', {
            'target_mean': panel['target_mean'], 'target_scale': panel['target_scale'],
        })
        save_json(cache / 'provenance.json', {
            'baseline': str(args.baseline_directory.resolve()),
        })
    report = {
        'created_at': datetime.now().astimezone().isoformat(),
        'baseline': str(args.baseline_directory.resolve()),
        'precision': 'float32', 'batch_size': 512, 'gpu_ids': devices,
        'steps_per_phase': args.steps, 'repeats': args.repeats, 'runs': [],
        'baseline_epoch_median_seconds': statistics.median(r['seconds'] for r in baseline['epochs']),
        'samples': {name: int(panel['masks'][name].sum()) for name in ('train', 'validation')},
    }
    print('Warm up both paths', flush=True)
    for backend in ('legacy', 'resident'):
        measure(panel, initial, devices, 512, 10, backend, 42)
    for repeat in range(args.repeats):
        measurements, weights = {}, {}
        for backend in (('legacy', 'resident') if repeat % 2 == 0 else ('resident', 'legacy')):
            measurement, weights[backend] = measure(
                panel, initial, devices, 512, args.steps, backend, 100 + repeat,
                sample_gpu=args.sample_gpu,
            )
            measurements[backend] = measurement
            print(repeat, backend, measurement, flush=True)
        max_weight_error = max(float((weights['legacy'][key] - weights['resident'][key]).abs().max())
                               for key in weights['legacy'])
        # Reduction ordering may differ; compare actual learned parameters,
        # not just loss being finite.
        for key in weights['legacy']:
            torch.testing.assert_close(weights['resident'][key], weights['legacy'][key],
                                       rtol=2e-4, atol=2e-5)
        report['runs'].append({
            'repeat': repeat, **measurements, 'max_absolute_weight_error': max_weight_error,
        })
        save_json(args.output_directory / 'benchmark.json', report)
        render_report(args.output_directory, report)
    medians = {
        backend: statistics.median(row[backend]['seconds'] for row in report['runs'])
        for backend in ('legacy', 'resident')
    }
    report.update(median_seconds=medians, speedup=medians['legacy'] / medians['resident'],
                  numerical_check='passed', selected_backend=(
                      'resident' if medians['resident'] < medians['legacy'] else 'legacy'))
    if args.profile:
        for backend in ('legacy', 'resident'):
            measure(panel, initial, devices, 512, 10, backend, 42,
                    args.output_directory / (backend + '-trace.json'))
    save_json(args.output_directory / 'benchmark.json', report)
    print('FINAL', report['speedup'], report['selected_backend'], flush=True)


if __name__ == '__main__':
    main()
