from copy import deepcopy
from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from research.fractional_forecast import DifferencingError
from research.fractional_results import chinese_result
from tools.compare_fractional_experiments import compare
from tools.run_fractional_research import _append_checkpoint, _restore_checkpoint
from market_data.price_basis import research_price_contract


class FractionalResultLanguageTests(SimpleTestCase):
    def test_translates_nested_fields_without_changing_weights_or_values(self):
        result = {
            'models': {
                '600001.SH:de_prado': {
                    'method': 'de_prado', 'training_device': 'cuda:0',
                    'model': {'output.weight': [[0.125]], 'output.bias': [0.5]},
                },
            },
            'backtests': {'de_prado': {'total_return': 0.1, 'trades': [
                {'side': 'BUY', 'instrument': '600001.SH', 'date': '2025-01-01'},
            ]}},
            'forecasts': {'log_return': [
                {'date': '2025-01-01', 'instrument': '600001.SH', 'predicted_return': 0.02},
            ]},
        }
        translated = chinese_result(result)
        model = translated['模型结果']['600001.SH:de_prado']
        self.assertEqual(model['方法'], '分数差分LSTM')
        self.assertEqual(model['训练设备'], 'cuda:0')
        self.assertEqual(model['模型权重'], result['models']['600001.SH:de_prado']['model'])
        backtest = translated['回测结果']['分数差分LSTM']
        self.assertEqual(backtest['累计收益率'], 0.1)
        self.assertEqual(backtest['成交记录'][0]['买卖方向'], '买入')
        self.assertEqual(translated['逐日预测']['普通收益率LSTM'][0]['预测收益率'], 0.02)
        self.assertIn('models', result)

    def test_localization_is_idempotent(self):
        result = {'forecasts': {'de_prado': [
            {'instrument': '600001.SH', 'predicted_return': 0.1},
        ]}, 'status': 'method_migration_not_exact_replication'}
        localized = chinese_result(result)
        self.assertEqual(chinese_result(localized), localized)


class FractionalComparisonTests(SimpleTestCase):
    def result(self):
        metrics = {
            'total_return': 0.1, 'annualized_return': 0.01, 'max_drawdown': -0.1,
            'sharpe_zero_risk_free': 0.5, 'costs': 100, 'order_count': 10,
            'missing_forecasts': 0, 'equity_curve': [{'equity': 110000}],
        }
        return {
            'parameters': {
                'train_start': '2006-10-16', 'validation_start': '2014-10-14',
                'test_start': '2016-10-14', 'test_end': '2026-10-14',
                'buy_cost': 0.0005, 'sell_cost': 0.001, 'initial_capital': 100000,
                'signal_threshold': 0.002, 'universe_size': 1, 'seed': 43,
            },
            'models': {'600001.SH:de_prado': {
                'seed': 42, 'training_device': 'cuda:0', 'trials': [
                    {'trial': {'hidden_size': 16, 'epochs': 30}, 'last_validation_mse_scaled': 0.1},
                ],
            }},
            'data_provenance': {'selected_instruments': ['600001.SH']},
            'backtests': {
                'de_prado': metrics, 'log_return': deepcopy(metrics),
                'database_random_equal_slot': {**metrics, 'total_return': 0.02},
            },
        }

    def test_mixed_languages_and_changed_losses_do_not_change_training_config(self):
        first = self.result()
        second = deepcopy(first)
        second['parameters']['seed'] = 44
        second['models']['600001.SH:de_prado']['trials'][0]['last_validation_mse_scaled'] = 0.9
        with TemporaryDirectory() as directory:
            paths = [Path(directory) / 'first.json', Path(directory) / 'second.json']
            paths[0].write_text(json.dumps(first), encoding='utf-8')
            paths[1].write_text(json.dumps(chinese_result(second)), encoding='utf-8')
            result = compare(paths)
        self.assertEqual(result['样本稳定性汇总']['分数差分LSTM']['跑赢基准样本组数'], 2)
        self.assertEqual(result['样本稳定性汇总']['分数差分LSTM']['平均年化收益率'], 0.01)
        self.assertEqual(result['股票池重合情况'][0]['重合股票数量'], 1)

    def test_changed_costs_or_model_seed_are_rejected(self):
        for change in ('cost', 'model_seed'):
            first = self.result()
            second = deepcopy(first)
            if change == 'cost':
                second['parameters']['buy_cost'] = 0.01
            else:
                second['models']['600001.SH:de_prado']['seed'] = 99
            with TemporaryDirectory() as directory:
                paths = [Path(directory) / 'first.json', Path(directory) / 'second.json']
                for path, data in zip(paths, (first, second)):
                    path.write_text(json.dumps(data), encoding='utf-8')
                with self.assertRaises(ValueError):
                    compare(paths)

    def test_branch_specific_frozen_models_are_supported(self):
        first = self.result()
        second_model = deepcopy(first['models']['600001.SH:de_prado'])
        second_model['trials'][0]['trial']['hidden_size'] = 64
        first['models']['600001.SH:log_return'] = second_model
        second = deepcopy(first)
        second['parameters']['seed'] = 44
        with TemporaryDirectory() as directory:
            paths = [Path(directory) / 'first.json', Path(directory) / 'second.json']
            for path, data in zip(paths, (first, second)):
                path.write_text(json.dumps(data), encoding='utf-8')
            self.assertEqual(len(compare(paths)['实验明细']), 2)

    def test_changed_early_stopping_or_selection_mode_is_rejected(self):
        for field, value in (
            ('early_stopping_patience', 15), ('selection_metric', 'return_mae'),
            ('training_mode', 'tuned'),
        ):
            first = self.result()
            second = deepcopy(first)
            second['parameters'][field] = value
            with TemporaryDirectory() as directory:
                paths = [Path(directory) / 'first.json', Path(directory) / 'second.json']
                for path, data in zip(paths, (first, second)):
                    path.write_text(json.dumps(data), encoding='utf-8')
                with self.assertRaises(ValueError):
                    compare(paths)

    def test_legacy_and_versioned_price_policies_cannot_be_compared(self):
        first = self.result()
        second = deepcopy(first)
        second['price_contract'] = research_price_contract()
        with TemporaryDirectory() as directory:
            paths = [Path(directory) / 'old.json', Path(directory) / 'new.json']
            for path, data in zip(paths, (first, second)):
                path.write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, '价格口径约定'):
                compare(paths)

    def test_changed_walk_forward_window_cannot_be_compared(self):
        first = self.result()
        first['parameters']['walk_forward_validation_days'] = 60
        second = deepcopy(first)
        second['parameters']['walk_forward_validation_days'] = 120
        with TemporaryDirectory() as directory:
            paths = [Path(directory) / 'first.json', Path(directory) / 'second.json']
            for path, data in zip(paths, (first, second)):
                path.write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, '滚动验证窗口'):
                compare(paths)


class FractionalTrainingCheckpointTests(SimpleTestCase):
    def test_checkpoint_with_changed_price_contract_is_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'progress.jsonl'
            _restore_checkpoint(path, 'signature')
            header = json.loads(path.read_text(encoding='utf-8'))
            header['price_contract']['model_input_basis'] = 'raw'
            path.write_text(json.dumps(header) + '\n', encoding='utf-8')
            with self.assertRaisesRegex(DifferencingError, 'price policy'):
                _restore_checkpoint(path, 'signature')

    def test_old_price_policy_checkpoint_is_rejected_without_modification(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'progress.jsonl'
            content = json.dumps({'type': 'header', 'version': 1, 'signature': 'signature'}) + '\n'
            path.write_text(content, encoding='utf-8')
            with self.assertRaisesRegex(DifferencingError, 'price policy'):
                _restore_checkpoint(path, 'signature')
            self.assertEqual(path.read_text(encoding='utf-8'), content)

    def test_checkpoint_restores_completed_symbol_models_and_forecasts(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'progress.jsonl'
            models, predictions, completed = _restore_checkpoint(path, 'signature')
            self.assertEqual(completed, set())

            method_results = {
                'de_prado': (
                    {'training_device': 'cuda:0'},
                    {(date(2025, 1, 2), '600001.SH'): 0.01},
                ),
                'log_return': (
                    {'training_device': 'cuda:1'},
                    {(date(2025, 1, 2), '600001.SH'): -0.02},
                ),
            }
            _append_checkpoint(path, '600001.SH', method_results)

            models, predictions, completed = _restore_checkpoint(path, 'signature')
            self.assertEqual(completed, {'600001.SH'})
            self.assertEqual(models['600001.SH:de_prado']['training_device'], 'cuda:0')
            self.assertEqual(
                predictions['log_return'][(date(2025, 1, 2), '600001.SH')], -0.02,
            )

    def test_checkpoint_rejects_a_different_experiment_signature(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'progress.jsonl'
            _restore_checkpoint(path, 'first')
            with self.assertRaises(DifferencingError):
                _restore_checkpoint(path, 'different')
