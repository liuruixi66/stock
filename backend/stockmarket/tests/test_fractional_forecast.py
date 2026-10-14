from datetime import date, timedelta
import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd

from research.fractional_forecast import (
    DifferencingError, ForecastConfig, HistoricalTopThirty, forecast_features,
    fractional_difference, fractional_weights, invert_one_step, long_only_signal,
    simulate_long_only, validate_prices,
)
from research.fractional_lstm import LSTMTrial, prepare_sequences, train_stock
from tools.download_fractional_prices import download
from tools.run_fractional_research import main as run_research


def weights(day=date(2023, 12, 31)):
    return pd.DataFrame([
        {'date': day, 'instrument': '000016.SHI', 'member_code': f'{600000 + i}.SH', 'weight': 2.0}
        for i in range(50)
    ])


def prices(days, symbols=('600000.SH',)):
    return pd.DataFrame([
        {'date': day, 'instrument': symbol, 'open': 10.0, 'high': 11.0,
         'low': 9.0, 'close': 10.0, 'volume': 1000}
        for day in days for symbol in symbols
    ])


def training_prices(start=date(2020, 1, 1), count=400):
    days = [start + timedelta(days=i) for i in range(count)]
    frame = prices(days)
    rng = np.random.default_rng(31)
    close = 10 * np.exp(np.cumsum(rng.normal(0, 0.01, len(days))))
    for field in ('open', 'close'):
        frame[field] = close
    frame['high'] = close * 1.01
    frame['low'] = close * 0.99
    return frame


CONFIG = ForecastConfig(
    train_start=date(2020, 1, 1), validation_start=date(2020, 9, 1),
    test_start=date(2020, 12, 1), test_end=date(2021, 1, 31),
    sequence_length=5, minimum_train_samples=20, minimum_validation_samples=10,
)


class FractionalForecastTests(unittest.TestCase):
    def test_integer_difference_and_inverse(self):
        values = np.arange(10, dtype=float)
        coefficients = fractional_weights(1)
        np.testing.assert_equal(coefficients, [1, -1])
        result = fractional_difference(values, coefficients)
        self.assertTrue(np.isnan(result[0]))
        np.testing.assert_equal(result[1:], np.ones(9))
        self.assertEqual(invert_one_step(1, values[:-1], coefficients), 9)

    def test_zero_and_tempered_difference(self):
        np.testing.assert_equal(fractional_weights(0), [1])
        coefficients = fractional_weights(0.5, tempering=0.2)
        self.assertAlmostEqual(coefficients[1], -0.5 * np.exp(-0.2))
        self.assertEqual(invert_one_step(7, [], fractional_weights(0)), 7)

    def test_fractional_inverse_matches_filter(self):
        values = np.sin(np.arange(200) / 10) + 4
        coefficients = fractional_weights(0.4)
        result = fractional_difference(values, coefficients)
        for index in range(len(coefficients), len(values)):
            self.assertAlmostEqual(invert_one_step(result[index], values[:index], coefficients), values[index])

    def test_future_suffix_cannot_change_features(self):
        original = np.arange(1, 151, dtype=float)
        future_changed = original.copy()
        future_changed[100:] *= 7
        coefficients = fractional_weights(0.5)
        first = forecast_features(pd.Series(original), fractional_difference(original, coefficients))
        second = forecast_features(pd.Series(future_changed), fractional_difference(future_changed, coefficients))
        pd.testing.assert_frame_equal(first.iloc[:100], second.iloc[:100])

    def test_sequences_use_target_date_and_training_only_scalers(self):
        frame = training_prices()
        first = prepare_sequences(frame, CONFIG, 1)
        altered = frame.copy()
        future = altered['date'] >= CONFIG.test_start
        altered.loc[future, ['open', 'high', 'low', 'close']] *= 3
        second = prepare_sequences(altered, CONFIG, 1)
        for name in ('x_mean', 'x_scale', 'y_mean', 'y_scale'):
            np.testing.assert_equal(first[name], second[name])
        np.testing.assert_equal(first['x'][first['train']], second['x'][second['train']])
        self.assertTrue(all(day < CONFIG.validation_start
                            for day, flag in zip(first['target_dates'], first['train']) if flag))
        boundary = first['target_dates'].index(CONFIG.validation_start)
        self.assertFalse(first['train'][boundary])
        self.assertTrue(first['validation'][boundary])

    def test_history_is_strictly_before_day_and_future_cannot_change_past(self):
        past = weights()
        future = weights(date(2024, 1, 3))
        future['weight'] = [1.0] * 30 + [3.5] * 20
        universe = HistoricalTopThirty(pd.concat([past, future]))
        self.assertEqual(universe.at(date(2024, 1, 3))[0], date(2023, 12, 31))
        self.assertEqual(universe.at(date(2024, 1, 2))[1], HistoricalTopThirty(past).at(date(2024, 1, 2))[1])
        self.assertEqual(len(universe.at(date(2024, 1, 4))[1]), 30)
        self.assertIn('600049.SH', universe.at(date(2024, 1, 4))[1])

    def test_incomplete_and_stale_weights_fail(self):
        with self.assertRaises(DifferencingError):
            HistoricalTopThirty(weights().iloc[:30])
        with self.assertRaises(DifferencingError):
            HistoricalTopThirty(weights()).at(date(2024, 2, 6))

    def test_universe_union_excludes_future_and_retired_training_members(self):
        universe = HistoricalTopThirty(pd.concat([weights(date(2023, 1, 1)), weights()]))
        self.assertEqual(len(universe.members_between(date(2024, 1, 1), date(2024, 1, 3))), 30)

    def test_band_keeps_previous_position(self):
        self.assertTrue(long_only_signal(0, True, 0.002))
        self.assertFalse(long_only_signal(0, False, 0.002))
        self.assertTrue(long_only_signal(0.01, False, 0.002))
        self.assertFalse(long_only_signal(-0.01, True, 0.002))

    def test_execution_is_next_open_with_real_fee_debit(self):
        days = [date(2024, 1, i) for i in (1, 2, 3)]
        universe = HistoricalTopThirty(weights())
        frame = prices(days, universe.at(days[0])[1])
        forecasts = {(day, '600000.SH'): 0.01 for day in days[:-1]}
        result = simulate_long_only(frame, forecasts, universe, days[0], days[-1])
        trade = result['trades'][0]
        self.assertEqual(trade['signal_date'], '2024-01-01')
        self.assertEqual(trade['date'], '2024-01-02')
        self.assertGreater(trade['cost'], 0)
        self.assertLess(result['total_return'], 0)

    def test_missing_held_price_is_not_a_fabricated_fill(self):
        days = [date(2024, 1, i) for i in (1, 2, 3)]
        universe = HistoricalTopThirty(weights())
        frame = prices(days, universe.at(days[0])[1])
        frame.loc[(frame['date'] == days[-1]) & (frame['instrument'] == '600000.SH'), 'volume'] = 0
        forecasts = {(days[0], '600000.SH'): 0.01}
        with self.assertRaisesRegex(DifferencingError, 'held price'):
            simulate_long_only(frame, forecasts, universe, days[0], days[-1])

    def test_invalid_inputs_do_not_succeed(self):
        with self.assertRaises(DifferencingError):
            fractional_weights(0.5, max_lags=2)
        frame = prices([date(2024, 1, 1)])
        frame['close'] = np.nan
        with self.assertRaises(DifferencingError):
            validate_prices(frame)
        with self.assertRaises(DifferencingError):
            LSTMTrial(epochs=0).validate()


class DownloadTests(unittest.TestCase):
    def test_serial_cached_download_uses_hfq_and_never_repeats_request(self):
        raw = pd.DataFrame({
            '日期': ['2024-01-01', '2024-01-02'], '开盘': [10, 10], '收盘': [10, 10],
            '最高': [11, 11], '最低': [9, 9], '成交量': [100, 100],
        })
        api = Mock(return_value=raw)
        module = SimpleNamespace(stock_zh_a_hist=api, __version__='mock')
        with TemporaryDirectory() as directory, patch.dict('sys.modules', {'akshare': module}), \
                patch('tools.download_fractional_prices.time.sleep') as sleep:
            root = Path(directory)
            source = root / 'weights.csv'
            weights().to_csv(source, index=False)
            download(source, root / 'cache', root / 'first.csv', date(2020, 1, 1),
                     date(2024, 1, 2), universe_start=date(2024, 1, 1))
            self.assertEqual(api.call_count, 30)
            self.assertEqual(sleep.call_count, 29)
            self.assertTrue(all(call.kwargs['adjust'] == 'hfq' for call in api.call_args_list))
            download(source, root / 'cache', root / 'second.csv', date(2020, 1, 1),
                     date(2024, 1, 2), universe_start=date(2024, 1, 1))
            self.assertEqual(api.call_count, 30)
            self.assertEqual((root / 'first.csv').read_bytes(), (root / 'second.csv').read_bytes())

    def test_failure_stops_without_retry_or_partial_combined_output(self):
        api = Mock(side_effect=OSError('rate limited'))
        with TemporaryDirectory() as directory, patch.dict('sys.modules', {
            'akshare': SimpleNamespace(stock_zh_a_hist=api, __version__='mock'),
        }):
            root = Path(directory)
            weights().to_csv(root / 'weights.csv', index=False)
            with self.assertRaisesRegex(OSError, 'rate limited'):
                download(root / 'weights.csv', root / 'cache', root / 'prices.csv',
                         date(2020, 1, 1), date(2024, 1, 2),
                         universe_start=date(2024, 1, 1))
            self.assertEqual(api.call_count, 1)
            self.assertFalse((root / 'prices.csv').exists())


@unittest.skipUnless(os.environ.get('FRACTIONAL_TORCH_SMOKE') == '1',
                     'Optional CPU LSTM smoke requires a verified PyTorch runtime')
class LSTMSmokeTests(unittest.TestCase):
    def test_actual_synthetic_training_and_future_independence(self):
        frame = training_prices()
        first, forecasts = train_stock(frame, CONFIG, 'log_return', [LSTMTrial(epochs=1)])
        altered = frame.copy()
        altered.loc[altered['date'] >= CONFIG.test_start, ['open', 'high', 'low', 'close']] *= 2
        second, _ = train_stock(altered, CONFIG, 'log_return', [LSTMTrial(epochs=1)])
        self.assertEqual(first['model'], second['model'])
        self.assertEqual(first['scaler'], second['scaler'])
        self.assertTrue(forecasts)
        self.assertTrue(all(np.isfinite(value) for value in forecasts.values()))
        de_prado, forecasts = train_stock(frame, CONFIG, 'de_prado', [LSTMTrial(epochs=1)])
        self.assertTrue(forecasts)
        self.assertIn('trials', de_prado['order_details'])

    def test_full_cli_with_synthetic_history_and_persistent_json(self):
        original = training_prices(date(2019, 1, 1), 780)
        frames = []
        for symbol in HistoricalTopThirty(weights()).at(date(2024, 1, 1))[1]:
            frame = original.copy()
            frame['instrument'] = symbol
            frames.append(frame)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            prices_path, weights_path = root / 'prices.csv', root / 'weights.csv'
            pd.concat(frames).to_csv(prices_path, index=False)
            pd.concat([weights(day) for day in [
                date(2020, 11, 30), date(2020, 12, 31), date(2021, 1, 31),
            ]]).to_csv(weights_path, index=False)
            metadata = root / 'prices.metadata.json'
            metadata.write_text(json.dumps({
                'source': 'SYNTHETIC_TEST_NOT_MARKET_DATA', 'adjustment': 'hfq',
                'prices_sha256': hashlib.sha256(prices_path.read_bytes()).hexdigest(),
                'weights_sha256': hashlib.sha256(weights_path.read_bytes()).hexdigest(),
            }), encoding='utf-8')
            output = root / 'result.json'
            argv = [
                'run_fractional_research', '--prices', str(prices_path),
                '--weights', str(weights_path), '--metadata', str(metadata),
                '--output', str(output), '--epochs', '1',
                '--train-start', '2019-01-01', '--validation-start', '2020-09-01',
                '--test-start', '2020-12-01', '--test-end', '2021-01-31',
            ]
            with patch('sys.argv', argv), patch('builtins.print'):
                run_research()
            result = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(len(result['models']), 60)
            self.assertEqual(len(result['backtests']), 3)
            self.assertTrue(all(run['missing_forecasts'] == 0 for run in result['backtests'].values()))
            self.assertEqual(len(result['backtests']['de_prado']['equity_curve']), 62)
            self.assertIn('model', result['models']['600000.SH:de_prado'])
