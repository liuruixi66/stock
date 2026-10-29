from copy import deepcopy
from datetime import date, timedelta
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless
from unittest.mock import patch
from xml.etree import ElementTree

from research.fractional_results import chinese_result
from tools.plot_fractional_research import (
    Report, financial_charts, generate, model_charts, svg_chart,
)


class FractionalChartTests(TestCase):
    def result(self):
        return {
            'parameters': {
                'seed': 42, 'initial_capital': 100000,
                'test_start': '2025-01-01', 'test_end': '2025-01-03',
            },
            'models': {
                f'600001.SH:{method}': {
                    'instrument': '600001.SH', 'method': method,
                    'validation_mse_scaled': 0.3, 'test_return_mae': 0.01,
                    'selected_model': {'epoch': 2},
                    'trials': [{
                        'trial': {'hidden_size': 16},
                        'last_validation_mse_scaled': 0.4,
                    }],
                } for method in ('de_prado', 'log_return')
            },
            'backtests': {
                method: {
                    'total_return': -0.1, 'annualized_return': -0.2,
                    'max_drawdown': -0.25, 'annualized_volatility': 0.3,
                    'sharpe_zero_risk_free': None, 'costs': 500,
                    'order_count': 10,
                    'equity_curve': [
                        {'date': '2025-01-01', 'equity': 100000},
                        {'date': '2025-01-02', 'equity': 120000},
                        {'date': '2025-01-03', 'equity': 90000},
                    ],
                } for method in ('de_prado', 'log_return', 'database_random_equal_slot')
            },
        }

    def test_generates_offline_chinese_report_for_both_schemas(self):
        for localized in (False, True):
            with self.subTest(localized=localized), TemporaryDirectory() as directory:
                root = Path(directory)
                source = root / 'result.json'
                data = self.result()
                source.write_text(json.dumps(chinese_result(data) if localized else data), encoding='utf-8')
                count = generate(source, root / 'report')
                self.assertEqual(count, 9)  # Four model charts, five available financial charts.
                html = (root / 'report' / 'index.html').read_text(encoding='utf-8')
                self.assertIn('不能还原收敛曲线', html)
                self.assertIn('未展示这些指标', html)
                self.assertIn('-25.00%', html)
                self.assertNotIn('<script', html)
                self.assertNotIn('https://', html)
                paths = list((root / 'report').glob('*.svg'))
                self.assertEqual(len(paths), count)
                for path in paths:
                    ElementTree.fromstring(path.read_text(encoding='utf-8'))
                with self.assertRaises(FileExistsError):
                    generate(source, root / 'report')

    def test_drawdown_includes_initial_capital_and_full_curve(self):
        class Capture:
            def __init__(self):
                self.calls = []
                self.sections = []

            def chart(self, title, description, series, categories, **options):
                self.calls.append((title, series, categories))
                return ''

            def section(self, title, cards):
                pass

        capture = Capture()
        data = chinese_result(self.result())
        data['回测结果']['分数差分LSTM']['净值曲线'][0]['总资产'] = 95000
        financial_charts(capture, data['回测结果'], 100000, '金融')
        self.assertEqual(capture.calls[0][1][0][1], [0.95, 1.2, 0.9])
        drawdown = capture.calls[1][1][0][1]
        for actual, expected in zip(drawdown, [-0.05, 0, -0.25]):
            self.assertAlmostEqual(actual, expected)
        self.assertEqual(len(capture.calls[0][2]), 3)

    def test_new_epoch_and_walk_forward_records_are_localized_and_plotted(self):
        data = self.result()
        for model in data['models'].values():
            model['trials'][0]['epoch_history'] = [
                {'epoch': 1, 'training_mse_scaled': 0.8, 'validation_mse_scaled': 0.9},
                {'epoch': 2, 'training_mse_scaled': 0.3, 'validation_mse_scaled': 0.4},
            ]
            model['daily_selections'] = [
                {'target_date': '2025-01-02', 'validation_mse_scaled': 0.5},
                {'target_date': '2025-01-03', 'validation_mse_scaled': 0.3},
            ]
        before = deepcopy(data)
        localized = chinese_result(data)
        with TemporaryDirectory() as directory:
            report = Report(Path(directory))
            model_charts(report, localized)
            self.assertEqual(report.count, 7)
            epoch_svg = (Path(directory) / 'chart-06.svg').read_text(encoding='utf-8')
            self.assertIn('<polyline', epoch_svg)
            self.assertIn('训练 MSE', epoch_svg)
        self.assertEqual(before, data)

    def test_evaluations_include_baselines_without_fabricating_missing_mape(self):
        data = chinese_result(self.result())
        metrics = {
            '平均绝对误差': 0.01, '均方根误差': 0.02,
            '方向准确率（百分比）': 60.0,
            '平均绝对百分比误差（百分比）': None,
            '对称平均绝对百分比误差（百分比）': 100.0,
        }
        data['模型效果评价'] = {'机器学习视角': {'预测方法评价': {
            '分数差分LSTM': {**metrics, '零收益预测基线': metrics},
        }}}
        with TemporaryDirectory() as directory:
            report = Report(Path(directory))
            model_charts(report, data)
            self.assertEqual(report.count, 7)
            self.assertIn('零基线', (Path(directory) / 'chart-05.svg').read_text(encoding='utf-8'))

    def test_invalid_values_and_unordered_dates_are_rejected(self):
        for series, days in (
            ([('model', [float('nan')])], ['2025-01-01']),
            ([('model', [1, 2])], ['2025-01-01']),
            ([('model', [1, 2])], ['2025-01-02', '2025-01-01']),
        ):
            with self.subTest(days=days), self.assertRaises(ValueError):
                svg_chart('test', series, days)

    def test_missing_values_are_gaps_and_labels_are_escaped(self):
        svg = svg_chart('<unsafe>', [('A&B', [1, None, 3])],
                        ['2025-01-01', '2025-01-02', '2025-01-03'])
        self.assertEqual(svg.count('<polyline'), 2)
        self.assertIn('&lt;unsafe&gt;', svg)
        self.assertIn('A&amp;B', svg)
        ElementTree.fromstring(svg)


class FractionalTrainingHistoryTests(TestCase):
    @skipUnless(importlib.util.find_spec('torch'), 'Optional research dependency: torch')
    def test_real_walk_forward_training_records_finite_epoch_losses(self):
        import numpy as np
        import pandas as pd
        import torch

        from research.fractional_forecast import ForecastConfig
        from research.fractional_lstm import LSTMTrial, train_stock

        days = [date(2024, 1, 1) + timedelta(days=i) for i in range(95)]
        close = 100 * np.exp(np.cumsum(0.002 * np.sin(np.arange(95)) + 0.0001))
        frame = pd.DataFrame({
            'date': days, 'instrument': '600001.SH', 'open': close,
            'high': close * 1.01, 'low': close * 0.99,
            'close': close, 'volume': 10000,
        })
        config = ForecastConfig(
            train_start=days[0], validation_start=days[65],
            test_start=days[92], test_end=days[94], sequence_length=3,
            minimum_train_samples=20, minimum_validation_samples=5,
        )
        previous_threads = torch.get_num_threads()
        previous_determinism = torch.are_deterministic_algorithms_enabled()
        try:
            with patch.object(torch.cuda, 'is_available', return_value=False):
                metadata, predictions = train_stock(
                    frame, config, 'log_return',
                    trials=[LSTMTrial(hidden_size=2, epochs=2, batch_size=16)],
                    walk_forward_validation_days=5,
                )
            history = metadata['trials'][0]['epoch_history']
            self.assertEqual(len(predictions), 3)
            self.assertEqual([p['epoch'] for p in history], [1, 2])
            for point in history:
                self.assertTrue(np.isfinite(point['training_mse_scaled']))
                self.assertTrue(np.isfinite(point['validation_mse_scaled']))
            self.assertEqual(
                history[-1]['validation_mse_scaled'],
                metadata['trials'][0]['last_validation_mse_scaled'],
            )
            self.assertEqual(len(chinese_result(metadata)['候选试验'][0]['逐轮训练记录']), 2)
        finally:
            torch.set_num_threads(previous_threads)
            torch.use_deterministic_algorithms(previous_determinism)
