import ast
import json
import math
from datetime import date, datetime, timedelta
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pandas as pd
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from stockmarket import bigquant_etf_rotation as adapter
from stockmarket.etf_rotation import build_rotation_targets
from stockmarket.test_etf_rotation import trending_history


class Store(dict):
    def init_once(self, **kwargs):
        for key, value in kwargs.items():
            self.setdefault(key, value)


def fund_frame(symbol='510300.SH', rate=0.002, count=220):
    bars = trending_history(rate=rate, count=count)
    frame = pd.DataFrame([
        {'date': bar.date, 'instrument': symbol, 'close': bar.close,
         'high': bar.high, 'low': bar.low, 'volume': bar.volume, 'amount': 30000000.0}
        for bar in bars
    ])
    return frame, bars


class FundHistoryTests(SimpleTestCase):
    def test_dated_fund_rows_match_portable_core(self):
        frame, bars = fund_frame()
        result = adapter.targets_from_fund_frame(frame, bars[-1].date)
        expected = build_rotation_targets({'510300.SH': bars}, bars[-1].date)
        self.assertEqual(result['selected'], expected['selected'])
        self.assertEqual(result['features'], expected['features'])
        self.assertAlmostEqual(result['weights']['510300.SH'], 0.4)
        self.assertEqual(result['rejected']['510500.SH'], 'missing_history')
        self.assertEqual(set(result['weights']), set(adapter.ETF_UNIVERSE))

    def test_future_row_cannot_change_current_signal(self):
        frame, bars = fund_frame()
        future = frame.iloc[[-1]].copy()
        future['date'] = bars[-1].date + timedelta(days=1)
        future['close'] = float('nan')
        future['amount'] = -1
        self.assertEqual(
            adapter.targets_from_fund_frame(frame, bars[-1].date),
            adapter.targets_from_fund_frame(pd.concat([frame, future]), bars[-1].date),
        )

    def test_out_of_order_query_rows_are_sorted_without_changing_targets(self):
        frame, bars = fund_frame()
        self.assertEqual(
            adapter.targets_from_fund_frame(frame, bars[-1].date),
            adapter.targets_from_fund_frame(frame.iloc[::-1], bars[-1].date),
        )

    def test_schema_duplicate_dates_and_invalid_amount_fail_explicitly(self):
        frame, bars = fund_frame()
        with self.assertRaisesRegex(ValueError, 'Missing'):
            adapter.targets_from_fund_frame(frame.drop(columns=['amount']), bars[-1].date)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            adapter.targets_from_fund_frame(pd.concat([frame, frame.iloc[[-1]]]), bars[-1].date)
        frame.loc[frame.index[-1], 'amount'] = float('nan')
        with self.assertRaisesRegex(ValueError, 'Invalid ETF amount'):
            adapter.targets_from_fund_frame(frame, bars[-1].date)

    def test_bad_data_is_not_a_cash_signal(self):
        frame, bars = fund_frame()
        for bad_frame in (frame.iloc[:10], frame.iloc[:-1],
                          frame.assign(amount=100), frame.assign(close=float('nan'))):
            with self.subTest(rows=len(bad_frame)), self.assertRaises(ValueError):
                adapter.targets_from_fund_frame(bad_frame, bars[-1].date)

    def test_non_numeric_market_fields_are_rejected_without_coercion(self):
        frame, bars = fund_frame()
        for field in ('close', 'amount'):
            invalid = frame.copy()
            invalid[field] = invalid[field].astype(object)
            invalid.loc[invalid.index[-1], field] = 'not a number'
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'Non-numeric'):
                adapter.targets_from_fund_frame(invalid, bars[-1].date)

    def test_valid_weak_trend_is_a_cash_signal(self):
        frame, bars = fund_frame(rate=-0.002)
        result = adapter.targets_from_fund_frame(frame, bars[-1].date)
        self.assertEqual(result['cash_weight'], 1)
        self.assertEqual(sum(result['weights'].values()), 0)

    def test_short_observed_coverage_is_explicitly_excluded(self):
        frame, bars = fund_frame(count=150)
        with self.assertRaisesRegex(ValueError, 'observed_history_under_180_days'):
            adapter.targets_from_fund_frame(frame, bars[-1].date)

    def test_query_is_bounded_and_uses_verified_fund_schema(self):
        frame, bars = fund_frame()
        dai = Mock()
        dai.query.return_value.df.return_value = frame
        with patch.object(adapter, 'import_module', return_value=dai) as load:
            pd.testing.assert_frame_equal(adapter.load_fund_history(bars[-1].date), frame)
        load.assert_called_once_with('dai')
        sql = dai.query.call_args.args[0]
        self.assertIn('FROM cn_fund_bar1d', sql)
        self.assertIn('amount', sql)
        self.assertNotIn('jqdata', sql)
        self.assertEqual(dai.query.call_args.kwargs['filters']['date'][-1],
                         bars[-1].date.isoformat())


class BigQuantExecutionTests(SimpleTestCase):
    def setUp(self):
        self.context = Mock()
        self.context.user_store = Store()
        self.context.user_store.init_once(**{
            adapter.STATE_KEY: None, adapter.SIGNAL_KEY: '', adapter.ATTEMPT_KEY: '',
        })
        self.context.get_open_orders.return_value = []
        self.positions = {}
        self.context.get_positions.side_effect = lambda: self.positions
        self.context.get_portfolio_value.return_value = 100000.0
        self.context.get_available_cash.return_value = 100000.0
        self.context.get_last_price.return_value = 10.0
        self.context.order.return_value = 0
        self.context.rebalance_period.is_signal_date.return_value = False
        self.data = Mock()
        self.data.current_dt = datetime(2024, 8, 7, 15)
        self.data.current.return_value = 1000000.0

    def hold(self, symbol='510300.SH', quantity=4000, available=None, value=None):
        self.positions[symbol] = SimpleNamespace(
            current_qty=quantity, avail_qty=quantity if available is None else available,
            market_value=quantity * 10 if value is None else value,
        )

    def test_initialize_preserves_json_state_across_daily_restart(self):
        pending = {'signal_date': '2024-08-06', 'weights': {'510300.SH': 0.4}}
        self.context.user_store[adapter.STATE_KEY] = pending
        bigtrader = Mock()
        with patch.object(adapter, 'import_module', return_value=bigtrader):
            adapter.initialize(self.context)
            adapter.initialize(self.context)
        self.assertEqual(self.context.user_store[adapter.STATE_KEY], pending)
        json.dumps(self.context.user_store)
        self.assertEqual(bigtrader.PerOrder.call_args.kwargs['tax_ratio'], 0)
        self.context.set_slippage_value.assert_called_with(
            slippage_type=2, slippage_value=0.002,
        )

    def test_reductions_must_fill_before_new_buys(self):
        self.hold()
        weights = {'510500.SH': 0.4}
        self.assertFalse(adapter.execute_targets(self.context, self.data, weights))
        self.context.order.assert_called_once_with('510300.SH', -4000)
        self.context.order.reset_mock()
        # An order return of 0 is only send success; the holding is unchanged.
        self.assertFalse(adapter.execute_targets(self.context, self.data, weights))
        self.context.order.assert_called_once_with('510300.SH', -4000)
        self.context.order.reset_mock()
        self.positions.clear()  # Simulate a later, confirmed sale.
        self.assertFalse(adapter.execute_targets(self.context, self.data, weights))
        self.context.order.assert_called_once_with('510500.SH', 3900)

    def test_pending_target_survives_restart_and_resumes_on_non_signal_day(self):
        self.hold()
        self.context.user_store[adapter.STATE_KEY] = {
            'signal_date': '2024-08-06', 'weights': {'510500.SH': 0.4},
        }
        adapter.handle_data(self.context, self.data)
        self.context.order.assert_called_once_with('510300.SH', -4000)
        self.context.order.reset_mock()
        self.positions.clear()
        self.data.current_dt += timedelta(days=1)
        bigtrader = Mock()
        with patch.object(adapter, 'import_module', return_value=bigtrader):
            adapter.initialize(self.context)
        adapter.handle_data(self.context, self.data)
        self.context.order.assert_called_once_with('510500.SH', 3900)
        self.hold('510500.SH', quantity=3900)
        self.context.order.reset_mock()
        self.data.current_dt += timedelta(days=1)
        adapter.handle_data(self.context, self.data)
        self.assertIsNone(self.context.user_store[adapter.STATE_KEY])
        self.context.order.assert_not_called()

    def test_same_day_callbacks_and_outstanding_orders_do_not_duplicate(self):
        self.context.user_store[adapter.STATE_KEY] = {
            'signal_date': '2024-08-06', 'weights': {'510300.SH': 0.4},
        }
        adapter.handle_data(self.context, self.data)
        adapter.handle_data(self.context, self.data)
        self.assertEqual(self.context.order.call_count, 1)
        self.context.order.reset_mock()
        self.data.current_dt += timedelta(days=1)
        self.context.get_open_orders.return_value = [object()]
        adapter.handle_data(self.context, self.data)
        self.context.order.assert_not_called()

    def test_failed_sale_logs_error_and_never_buys(self):
        self.hold()
        self.context.order.return_value = -2
        self.context.get_error_msg.return_value = 'insufficient sellable quantity'
        self.assertFalse(adapter.execute_targets(
            self.context, self.data, {'510500.SH': 0.4},
        ))
        self.context.order.assert_called_once_with('510300.SH', -4000)
        self.context.get_error_msg.assert_called_once_with(-2)
        self.assertIn('insufficient sellable quantity',
                      self.context.logger.warning.call_args.args[0])

    def test_t1_partial_quantity_and_zero_volume_prevent_new_buys(self):
        self.hold(available=0)
        self.assertFalse(adapter.execute_targets(
            self.context, self.data, {'510500.SH': 0.4},
        ))
        self.context.order.assert_not_called()
        self.hold(available=1000)
        self.assertFalse(adapter.execute_targets(
            self.context, self.data, {'510500.SH': 0.4},
        ))
        self.context.order.assert_called_once_with('510300.SH', -1000)
        self.context.order.reset_mock()
        self.data.current.return_value = 0
        self.assertFalse(adapter.execute_targets(
            self.context, self.data, {'510500.SH': 0.4},
        ))
        self.context.order.assert_not_called()

    def test_buy_reservations_use_only_current_cash_not_projected_sales(self):
        self.context.get_available_cash.return_value = 70000.0
        weights = {'510300.SH': 0.4, '510500.SH': 0.3, '159915.SZ': 0.25}
        self.assertFalse(adapter.execute_targets(self.context, self.data, weights))
        quantities = [call.args[1] for call in self.context.order.call_args_list]
        self.assertTrue(all(quantity > 0 and quantity % 100 == 0 for quantity in quantities))
        cost = sum(quantity * 10 * 1.005 + 5 for quantity in quantities)
        self.assertLessEqual(cost, 70000)
        self.assertLessEqual(sum(quantity * 10 for quantity in quantities), 95000)

    def test_failed_buy_stops_later_orders_and_remains_pending(self):
        self.context.order.return_value = -1
        self.assertFalse(adapter.execute_targets(
            self.context, self.data, {'510300.SH': 0.4, '510500.SH': 0.3},
        ))
        self.assertEqual(self.context.order.call_count, 1)

    def test_small_exit_is_not_blocked_by_turnover_threshold(self):
        self.hold(quantity=100)
        self.assertFalse(adapter.execute_targets(self.context, self.data, {}))
        self.context.order.assert_called_once_with('510300.SH', -100)

    def test_tiny_budget_and_sub_lot_reductions_do_not_loop_forever(self):
        self.context.get_portfolio_value.return_value = 100
        self.context.get_available_cash.return_value = 100
        self.assertTrue(adapter.execute_targets(
            self.context, self.data, {'510300.SH': 0.4},
        ))
        self.context.order.assert_not_called()
        self.context.get_portfolio_value.return_value = 1000
        self.hold(quantity=100)
        self.assertTrue(adapter.execute_targets(
            self.context, self.data, {'510300.SH': 0.4},
        ))
        self.context.order.assert_not_called()

    def test_bad_weights_or_unrelated_positions_never_place_orders(self):
        for weights in ({'510300.SH': -0.1}, {'510300.SH': math.nan},
                        {'510300.SH': 0.5}, {'UNKNOWN': 0.1},
                        {symbol: 0.4 for symbol in adapter.ETF_UNIVERSE[:3]}):
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                adapter.execute_targets(self.context, self.data, weights)
        self.hold('600519.SH')
        with self.assertRaisesRegex(ValueError, 'dedicated'):
            adapter.execute_targets(self.context, self.data, {})
        self.context.order.assert_not_called()

    def test_expired_targets_are_cleared_without_orders(self):
        self.context.user_store[adapter.STATE_KEY] = {
            'signal_date': '2024-07-01', 'weights': {'510300.SH': 0.4},
        }
        adapter.handle_data(self.context, self.data)
        self.assertIsNone(self.context.user_store[adapter.STATE_KEY])
        self.context.order.assert_not_called()

    def test_daily_signal_loads_only_current_completed_bar_date(self):
        frame, bars = fund_frame()
        self.data.current_dt = datetime.combine(bars[-1].date, datetime.min.time())
        self.context.rebalance_period.is_signal_date.return_value = True
        with patch.object(adapter, 'load_fund_history', return_value=frame) as load:
            adapter.handle_data(self.context, self.data)
            adapter.handle_data(self.context, self.data)
        load.assert_called_once_with(bars[-1].date)
        self.context.rebalance_period.is_signal_date.assert_called_with(bars[-1].date)
        self.assertEqual(self.context.order.call_count, 1)

    def test_held_missing_data_is_error_not_liquidation(self):
        frame, bars = fund_frame()
        self.hold('510500.SH')
        self.context.rebalance_period.is_signal_date.return_value = True
        self.data.current_dt = datetime.combine(bars[-1].date, datetime.min.time())
        with patch.object(adapter, 'load_fund_history', return_value=frame):
            with self.assertRaisesRegex(ValueError, 'Held ETF data unavailable'):
                adapter.handle_data(self.context, self.data)
        self.context.order.assert_not_called()


class BigQuantExportTests(SimpleTestCase):
    def test_command_exports_parseable_source_without_local_or_joinquant_imports(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / 'bigquant.py'
            call_command('export_bigquant_etf', '--output', str(output), stdout=StringIO())
            content = output.read_text(encoding='utf-8')
            ast.parse(content, feature_version=(3, 8))
            self.assertNotIn('from stockmarket', content)
            self.assertNotIn('jqdata', content)
            self.assertIn('def handle_data(', content)
            self.assertIn('performance = run_backtest()', content)
            with self.assertRaisesRegex(CommandError, 'overwrite'):
                call_command('export_bigquant_etf', '--output', str(output))
            self.assertEqual(output.read_text(encoding='utf-8'), content)

    def test_runner_uses_daily_fund_weekly_next_open_settings(self):
        modules = Mock()
        with patch.object(adapter, 'import_module', return_value=modules):
            adapter.run_backtest('2024-01-01', '2024-08-01', 100000)
        kwargs = modules.M.bigtrader.v30.call_args.kwargs
        self.assertEqual(kwargs['data']['market'], 'cn_fund')
        self.assertEqual(kwargs['data']['instruments'], list(adapter.ETF_UNIVERSE))
        self.assertEqual(kwargs['product_type'], '基金')
        self.assertEqual(kwargs['frequency'], 'daily')
        self.assertEqual(kwargs['rebalance_period_type'], '周度交易日')
        self.assertEqual(kwargs['rebalance_period_days'], '1')
        self.assertEqual(kwargs['order_price_field_buy'], 'open')
        self.assertEqual(kwargs['order_price_field_sell'], 'open')
        self.assertEqual(kwargs['before_start_days'], 250)

    def test_runner_rejects_future_dates_and_nonfinite_capital(self):
        with self.assertRaises(ValueError):
            adapter.run_backtest(end_date=date.today().isoformat())
        with self.assertRaises(ValueError):
            adapter.run_backtest(capital_base=float('nan'))
