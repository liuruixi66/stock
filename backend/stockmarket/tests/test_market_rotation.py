from contextlib import closing
from dataclasses import replace
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd

from research.market_rotation import (
    RotationConfig, prepare_panel, select_targets, simulate_rotation, temporal_split,
)
from tools.run_market_rotation import (
    load_market, parallel_devices, replace_report_file, report, select_device,
)
from research.prediction_metrics import evaluate_return_predictions
from tools.market_rotation_dashboard import render_dashboard


class RotationTests(TestCase):
    def test_dashboard_loading_empty_curves_and_escaped_diagnostics(self):
        state = {
            'status': 'loading_frozen_market_snapshot', 'epochs': [],
            'updated_at': '2026-10-27', 'requested_epochs': 20, 'gpu_ids': [0, 1],
            'loading': {'loaded': 2500, 'total': 5000}, 'error': '<script>bad</script>',
        }
        html = render_dashboard(state)
        self.assertIn('正在装载行情', html)
        self.assertIn('2,500 / 5,000', html)
        self.assertIn('双卡并行', html)
        self.assertIn('value="50.00"', html)
        self.assertIn('尚无完整训练轮次', html)
        self.assertIn('<details>', html)
        self.assertNotIn('<svg', html)
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_dashboard_real_charts_and_failed_refresh(self):
        state = {
            'status': 'completed', 'updated_at': '2026-10-27',
            'epochs': [{'epoch': 1, 'train_mse': 1., 'validation_mse': 2.}],
            'validation': {'curve': [
                {'date': '2025-01-02', 'equity': 100000., 'drawdown': 0.},
                {'date': '2025-01-03', 'equity': 99000., 'drawdown': -.01},
            ]},
        }
        html = render_dashboard(state)
        self.assertEqual(html.count('<svg'), 3)
        self.assertIn('lang="zh-CN"', html)
        self.assertNotIn('http-equiv="refresh"', html)

    def test_multi_gpu_selection_validates_all_requested_devices(self):
        torch = Mock()
        torch.cuda.is_available.return_value = True
        torch.cuda.device_count.return_value = 2
        _, indices = parallel_devices('auto', [0, 1], torch)
        self.assertEqual(indices, [0, 1])
        for requested, indices in (
            ('cpu', [0, 1]), ('auto', [0]), ('auto', [0, 0]),
            ('auto', [-1, 0]), ('auto', [0, 2]),
        ):
            with self.subTest(indices=indices), self.assertRaises(ValueError):
                parallel_devices(requested, indices, torch)

    def test_return_metrics_and_invalid_values(self):
        metrics = evaluate_return_predictions([0, .1, -.1], [0, .05, -.05])
        self.assertAlmostEqual(metrics['mae'], .1 / 3)
        self.assertAlmostEqual(metrics['rmse'], np.sqrt(.005 / 3))
        self.assertEqual(metrics['directional_accuracy_percent'], 100)
        self.assertEqual(metrics['mape_sample_count'], 2)
        self.assertIsNone(evaluate_return_predictions([0], [0])['mape_percent'])
        for actual, predicted in (([], []), ([1], [1, 2]), ([float('nan')], [0])):
            with self.assertRaises(ValueError):
                evaluate_return_predictions(actual, predicted)

    def test_atomic_report_retries_only_temporary_permission_errors(self):
        temporary = Mock()
        temporary.replace.side_effect = [PermissionError('locked'), None]
        with patch('tools.run_market_rotation.time.sleep'):
            replace_report_file(temporary, Path('report.json'))
        self.assertEqual(temporary.replace.call_count, 2)
        temporary.replace.side_effect = PermissionError('permanently locked')
        with patch('tools.run_market_rotation.time.sleep'), self.assertRaises(PermissionError):
            replace_report_file(temporary, Path('report.json'))

    def test_explicit_cuda_never_silently_falls_back(self):
        torch = Mock()
        torch.cuda.is_available.return_value = False
        torch.cuda.device_count.return_value = 0
        with self.assertRaisesRegex(ValueError, 'CPU fallback is disabled'):
            select_device('cuda:1', torch)
        torch.device.assert_not_called()
        torch.cuda.is_available.return_value = True
        torch.cuda.device_count.return_value = 2
        select_device('cuda:1', torch)
        torch.device.assert_called_once_with('cuda:1')
        for invalid in ('cuda', 'cuda:-1', 'gpu', 'cuda:2'):
            with self.subTest(device=invalid), self.assertRaises(ValueError):
                select_device(invalid, torch)

    def test_temporal_labels_purge_boundary_crossings(self):
        config = RotationConfig()
        self.assertEqual(temporal_split('2023-12-20', '2023-12-27', config), 'train')
        self.assertIsNone(temporal_split('2023-12-28', '2024-01-05', config))
        self.assertIsNone(temporal_split('2025-12-29', '2026-01-06', config))
        self.assertEqual(temporal_split('2024-01-02', '2024-01-09', config), 'validation')
        self.assertEqual(temporal_split('2026-01-02', '2026-01-09', config), 'test')
        self.assertIsNone(temporal_split('2026-10-23', None, config))

    def test_retention_and_six_replacements(self):
        config = RotationConfig()
        holdings = [f'old{i}' for i in range(30)]
        ranked = [(f'new{i}', 0.1) for i in range(60)]
        selected, _ = select_targets(ranked, holdings, config, 0, True)
        self.assertEqual(len(selected), 30)
        self.assertEqual(len(set(selected) - set(holdings)), 6)
        selected, _ = select_targets(ranked, [], config, 0, False)
        self.assertEqual(len(selected), 30)
        selected, _ = select_targets([(s, .1) for s in holdings], holdings, config, 0, True)
        self.assertEqual(set(selected), set(holdings))

    def market(self):
        sessions = pd.bdate_range('2026-01-01', periods=16).strftime('%Y-%m-%d').tolist()
        rows = [{'day': day, 'symbol': symbol, 'open': 10.0, 'high': 11.,
                 'low': 9., 'close': 10., 'factor': 1., 'volume': 100.,
                 'suspended': False, 'up_limit': 11., 'down_limit': 9.}
                for day in sessions for symbol in ('A', 'B')]
        return pd.DataFrame(rows), sessions

    def test_next_session_only_and_exposure(self):
        prices, sessions = self.market()
        scores = {day: {'A': .1} for day in sessions}
        result = simulate_rotation(prices, scores, sessions, sessions[0], sessions[-1],
                                   replace(RotationConfig(), slots=1, replacements=1), 0)
        self.assertEqual(result['trades'][0]['date'], '2026-01-05')
        self.assertEqual(result['trades'][0]['signal_date'], '2026-01-02')
        self.assertTrue(all(row['exposure'] <= .95000001 for row in result['curve']))
        self.assertTrue(all(row['cash'] >= -1e-8 for row in result['curve']))

    def test_suspension_freezes_holdings_and_limits_block_buy(self):
        prices, sessions = self.market()
        prices.loc[(prices.symbol == 'A') & (prices.day >= '2026-01-12'), 'suspended'] = True
        scores = {day: {'A': .1} if day < '2026-01-09' else {'B': .2}
                  for day in sessions}
        config = replace(RotationConfig(), slots=1, replacements=1)
        result = simulate_rotation(prices, scores, sessions, sessions[0], sessions[-1],
                                   config, 0)
        self.assertEqual(result['unresolved_terminal_holdings'], ['A'])
        self.assertFalse(any(row['side'] == 'SELL' for row in result['trades']))
        self.assertFalse(any(row['symbol'] == 'B' for row in result['trades']))
        prices.loc[prices.symbol == 'A', 'up_limit'] = 10
        result = simulate_rotation(prices, {d: {'A': .1} for d in sessions}, sessions,
                                   sessions[0], sessions[-1], config, 0)
        self.assertEqual(result['trades'], [])

    def test_training_scaler_is_invariant_to_future_prices(self):
        sessions = pd.bdate_range('2023-01-02', '2026-04-01').strftime('%Y-%m-%d').tolist()
        close = 10 * np.exp(np.arange(len(sessions)) * .001
                            + np.sin(np.arange(len(sessions))) * .01)
        prices = pd.DataFrame({
            'symbol': 'A', 'day': sessions, 'open': close, 'high': close * 1.01,
            'low': close * .99, 'close': close, 'factor': 1., 'volume': 100.,
        })
        baseline = prepare_panel(prices, sessions, RotationConfig())
        changed = prices.copy()
        future = changed.day >= '2024-01-01'
        changed.loc[future, ['open', 'high', 'low', 'close']] *= 10
        changed.loc[future, 'volume'] *= 10
        altered = prepare_panel(changed, sessions, RotationConfig())
        np.testing.assert_array_equal(baseline['mean'], altered['mean'])
        np.testing.assert_array_equal(baseline['scale'], altered['scale'])
        self.assertEqual(baseline['target_mean'], altered['target_mean'])
        self.assertEqual(baseline['target_scale'], altered['target_scale'])
        mask = baseline['masks']['train']
        np.testing.assert_array_equal(baseline['y'][mask], altered['y'][mask])
        test_changed = prices.copy()
        test_changed.loc[test_changed.day >= '2026-01-01',
                         ['open', 'high', 'low', 'close']] *= 100
        held_out = prepare_panel(test_changed, sessions, RotationConfig())
        np.testing.assert_array_equal(baseline['mean'], held_out['mean'])
        train_validation = baseline['masks']['train'] | baseline['masks']['validation']
        np.testing.assert_array_equal(baseline['y'][train_validation],
                                      held_out['y'][train_validation])
        for end in baseline['ends'][train_validation]:
            np.testing.assert_array_equal(baseline['features'][end - 19:end + 1],
                                          held_out['features'][end - 19:end + 1])

    def test_future_suspension_does_not_rerank_signal(self):
        prices, sessions = self.market()
        prices.loc[(prices.symbol == 'A') & (prices.day == '2026-01-05'), 'suspended'] = True
        result = simulate_rotation(
            prices, {day: {'A': .2, 'B': .1} for day in sessions}, sessions,
            sessions[0], sessions[-1],
            replace(RotationConfig(), slots=1, replacements=1), 0,
        )
        selection = next(row for row in result['selections'] if row['date'] == '2026-01-05')
        self.assertEqual(selection['symbols'], ['A'])
        self.assertFalse(any(row['date'] == '2026-01-05' for row in result['trades']))

    def test_calendar_gap_never_becomes_five_session_label(self):
        sessions = pd.bdate_range('2023-01-02', '2026-04-01').strftime('%Y-%m-%d').tolist()
        values = 10 + np.sin(np.arange(len(sessions))) + np.arange(len(sessions)) * .01
        prices = pd.DataFrame({
            'symbol': 'A', 'day': sessions, 'open': values, 'high': values + 1,
            'low': values - 1, 'close': values, 'factor': 1., 'volume': 100.,
        })
        gap = sessions.index('2025-03-03')
        prices = prices[prices.day != sessions[gap]]
        panel = prepare_panel(prices, sessions, RotationConfig())
        before_gap = next(row for row in panel['metadata'] if row[1] == sessions[gap - 1])
        self.assertIsNone(before_gap[2])
        self.assertIsNone(before_gap[3])

    def test_live_report_has_no_fabricated_curves(self):
        with TemporaryDirectory() as directory:
            path = Path(directory)
            state = {'status': 'training', 'updated_at': '2026-10-27', 'epochs': []}
            report(path, state)
            html = (path / 'index.html').read_text(encoding='utf-8')
            self.assertNotIn('<svg', html)
            self.assertIn('http-equiv="refresh"', html)
            self.assertEqual(json.loads((path / 'progress.json').read_text()), state)
            state.update(status='failed', error='Explicit input error')
            report(path, state)
            html = (path / 'index.html').read_text(encoding='utf-8')
            self.assertIn('Explicit input error', html)
            self.assertNotIn('http-equiv="refresh"', html)

    def test_readonly_loader_freezes_missing_limits_and_rejects_missing_factor(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / 'market.db'
            with closing(sqlite3.connect(database)) as conn:
                conn.executescript('''
                    CREATE TABLE ts_daily (
                        ts_code,trade_date,open,high,low,close,vol);
                    CREATE TABLE ts_adj_factor (ts_code,trade_date,adj_factor);
                    CREATE TABLE ts_stk_limit (ts_code,trade_date,up_limit,down_limit);
                    CREATE TABLE ts_suspend_d (ts_code,trade_date,suspend_type);
                    CREATE TABLE ts_stock_basic (ts_code,exchange,list_date,delist_date);
                    CREATE TABLE ts_trade_cal (exchange,cal_date,is_open);
                    INSERT INTO ts_stock_basic VALUES ('000001.SZ','SZSE','19900101',NULL);
                    INSERT INTO ts_daily VALUES ('000001.SZ','20260105',10,11,9,10,100);
                    INSERT INTO ts_adj_factor VALUES ('000001.SZ','20260105',1);
                    INSERT INTO ts_stk_limit VALUES ('other','20260105',11,9);
                    INSERT INTO ts_suspend_d VALUES ('other','20260105','S');
                    INSERT INTO ts_trade_cal VALUES ('SSE','20260105',1);
                ''')
            original = database.read_bytes()
            prices, _, provenance = load_market(database, RotationConfig())
            self.assertEqual(provenance['missing_limit_rows_frozen'], 1)
            self.assertTrue(prices.iloc[0]['suspended'])
            self.assertEqual(original, database.read_bytes())
            with closing(sqlite3.connect(database)) as conn:
                conn.execute('UPDATE ts_adj_factor SET adj_factor=NULL')
                conn.commit()
            with self.assertRaisesRegex(ValueError, 'adjustment'):
                load_market(database, RotationConfig())
