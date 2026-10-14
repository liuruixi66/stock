import ast
import importlib.util
import math
import sys
import types
import unittest
from dataclasses import replace
from datetime import date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from strategies import etf_rotation
from strategies.etf_rotation import RotationBar
from strategies.etf_rotation import RotationConfig
from strategies.etf_rotation import build_rotation_targets
from strategies.etf_rotation import shrink_to_equal


def trending_history(rate=0.002, count=150, oscillation=0.004):
    bars = []
    close = 10.0
    start = date(2024, 1, 1)
    for index in range(count):
        close *= 1 + rate + oscillation * math.sin(index)
        bars.append(RotationBar(start + timedelta(days=index), close,
                                close * 1.01, close * 0.99, 1000000.0))
    return bars


class RotationRulesTests(unittest.TestCase):
    def setUp(self):
        self.bars = trending_history()
        self.as_of = self.bars[-1].date

    def test_long_only_caps_and_cash_accounting(self):
        histories = {str(index): trending_history(0.001 + index * 0.0003)
                     for index in range(6)}
        result = build_rotation_targets(histories, self.as_of)
        self.assertEqual(len(result['selected']), 3)
        self.assertTrue(all(0 <= weight <= 0.4 for weight in result['weights'].values()))
        self.assertLessEqual(sum(result['weights'].values()), 0.95)
        self.assertAlmostEqual(sum(result['weights'].values()) + result['cash_weight'], 1)
        self.assertEqual(len([w for w in result['weights'].values() if w > 0]), 3)

    def test_only_one_candidate_leaves_sixty_percent_cash(self):
        result = build_rotation_targets({'ETF': self.bars}, self.as_of)
        self.assertAlmostEqual(result['weights']['ETF'], 0.4)
        self.assertAlmostEqual(result['cash_weight'], 0.6)

    def test_bad_trend_is_cash_not_short(self):
        result = build_rotation_targets({'ETF': trending_history(-0.002)}, self.as_of)
        self.assertEqual(result['features']['ETF']['regime'], 'weak')
        self.assertEqual(result['weights']['ETF'], 0)
        self.assertEqual(result['cash_weight'], 1)

    def test_recent_shock_excludes_asset(self):
        shocked = self.bars[:-1] + [replace(
            self.bars[-1], close=self.bars[-2].close * 0.90,
            low=self.bars[-2].close * 0.89,
        )]
        result = build_rotation_targets({'ETF': shocked}, self.as_of)
        self.assertEqual(result['features']['ETF']['regime'], 'stress')
        self.assertEqual(result['weights']['ETF'], 0)

    def test_thin_volume_excludes_asset(self):
        bars = self.bars[:-1] + [replace(self.bars[-1], volume=100)]
        result = build_rotation_targets({'ETF': bars}, self.as_of)
        self.assertEqual(result['features']['ETF']['regime'], 'thin')
        self.assertEqual(result['weights']['ETF'], 0)

    def test_future_mutations_cannot_change_signal(self):
        before = build_rotation_targets({'ETF': self.bars}, self.as_of)
        future = RotationBar(self.as_of + timedelta(days=1), float('nan'), -1, -2, -1)
        after = build_rotation_targets({'ETF': self.bars + [future]}, self.as_of)
        self.assertEqual(before, after)

    def test_rejections_are_explicit_and_do_not_pollute_valid_asset(self):
        histories = {
            'valid': self.bars,
            'short': self.bars[-10:],
            'stale': self.bars[:-1],
            'duplicate': self.bars + [self.bars[-1]],
            'unsorted': list(reversed(self.bars)),
            'nan': self.bars[:-1] + [replace(self.bars[-1], close=float('nan'))],
            'zero': self.bars[:-1] + [replace(self.bars[-1], volume=0)],
            'constant': [replace(bar, close=10, high=11, low=9) for bar in self.bars],
        }
        result = build_rotation_targets(histories, self.as_of)
        self.assertEqual(result['selected'], ['valid'])
        self.assertEqual(result['rejected']['short'], 'insufficient_history')
        self.assertEqual(result['rejected']['stale'], 'stale_history')
        self.assertEqual(result['rejected']['duplicate'], 'duplicate_or_unsorted_dates')
        self.assertEqual(result['rejected']['unsorted'], 'duplicate_or_unsorted_dates')
        self.assertEqual(result['rejected']['nan'], 'invalid_ohlcv')
        self.assertEqual(result['rejected']['zero'], 'inactive_or_zero_volatility')
        self.assertEqual(result['rejected']['constant'], 'inactive_or_zero_volatility')

    def test_volatility_budget_is_measured_not_just_gross_cap(self):
        histories = {str(index): trending_history(0.004 + index * 0.0002,
                                                 oscillation=0.025)
                     for index in range(3)}
        config = RotationConfig(target_volatility=0.05)
        result = build_rotation_targets(histories, self.as_of, config)
        weighted_volatility = sum(
            weight * result['features'][symbol]['annual_volatility']
            for symbol, weight in result['weights'].items()
        )
        self.assertGreater(weighted_volatility, 0)
        self.assertLessEqual(weighted_volatility, config.target_volatility + 1e-12)

    def test_shrinkage_endpoints_and_existing_formula(self):
        weights = {'A': 0.9, 'B': 0.1}
        self.assertEqual(shrink_to_equal(weights, 0), weights)
        self.assertEqual(shrink_to_equal(weights, 1), {'A': 0.5, 'B': 0.5})
        self.assertAlmostEqual(shrink_to_equal(weights, 0.5)['A'], 0.7)
        self.assertEqual(shrink_to_equal({}, 0.5), {})
        with self.assertRaises(ValueError):
            shrink_to_equal(weights, float('nan'))

    def test_bad_configuration_and_empty_universe_raise(self):
        for config in (RotationConfig(shrinkage=-1), RotationConfig(holdings=0),
                       RotationConfig(short_window=60), RotationConfig(max_weight=2),
                       RotationConfig(target_volatility=float('nan'))):
            with self.subTest(config=config), self.assertRaises(ValueError):
                build_rotation_targets({'ETF': self.bars}, self.as_of, config)
        with self.assertRaises(ValueError):
            build_rotation_targets({}, self.as_of)


class JoinQuantExecutionTests(unittest.TestCase):
    def setUp(self):
        fake = types.ModuleType('jqdata')
        fake.g = SimpleNamespace(rotation_config=RotationConfig(),
                                 rebalance_threshold=0.03)
        fake.log = Mock()
        fake.get_open_orders = Mock(return_value={})
        fake.get_current_data = Mock()
        fake.order_target_value = Mock()
        fake.record = Mock()
        fake.get_security_info = Mock()
        fake.get_price = Mock()
        for name in ('set_option', 'set_benchmark', 'set_order_cost', 'OrderCost',
                     'set_slippage', 'PriceRelatedSlippage', 'run_weekly'):
            setattr(fake, name, Mock())
        self.api = fake
        path = Path(etf_rotation.__file__).parent / 'platforms' / 'joinquant_etf_rotation.py'
        spec = importlib.util.spec_from_file_location('tested_joinquant_adapter', path)
        self.adapter = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'jqdata': fake}):
            spec.loader.exec_module(self.adapter)
        self.context = SimpleNamespace(
            previous_date=date(2024, 8, 1),
            portfolio=SimpleNamespace(total_value=100000.0, available_cash=100000.0,
                                      positions={}),
        )
        self.api.get_current_data.return_value = {
            symbol: SimpleNamespace(paused=False, last_price=10.0,
                                    low_limit=9.0, high_limit=11.0)
            for symbol in ('A', 'B', 'C', 'OLD')
        }
        self.api.order_target_value.side_effect = self.fill_order

    def fill_order(self, symbol, target):
        portfolio = self.context.portfolio
        old = portfolio.positions.get(symbol)
        previous = old.value if old else 0
        portfolio.available_cash -= target - previous
        if target == 0:
            portfolio.positions.pop(symbol, None)
        else:
            portfolio.positions[symbol] = SimpleNamespace(
                value=target, closeable_amount=int(target / 10), total_amount=int(target / 10),
            )
        return SimpleNamespace(filled=100, amount=100)

    def hold(self, symbol, value, closeable=None):
        amount = int(value / 10)
        self.context.portfolio.positions[symbol] = SimpleNamespace(
            value=value, total_amount=amount,
            closeable_amount=amount if closeable is None else closeable,
        )
        self.context.portfolio.available_cash -= value

    def test_initialize_has_weekly_schedule_real_price_costs_and_future_guard(self):
        self.adapter.initialize(self.context)
        self.api.set_option.assert_any_call('avoid_future_data', True)
        self.api.set_option.assert_any_call('use_real_price', True)
        self.api.run_weekly.assert_called_once_with(
            self.adapter.rebalance_etfs, weekday=1, time='10:00',
            reference_security='510300.XSHG',
        )
        self.assertEqual(self.api.set_order_cost.call_args.kwargs['type'], 'fund')
        self.assertEqual(self.api.OrderCost.call_args.kwargs['close_tax'], 0)
        self.assertEqual(self.api.PriceRelatedSlippage.call_args.args, (0.002,))

    def test_sells_before_buys_and_never_spends_more_than_cash(self):
        self.hold('OLD', 80000)
        self.adapter.execute_etf_targets(self.context, {'A': 0.4, 'B': 0.3, 'C': 0.25})
        calls = self.api.order_target_value.call_args_list
        self.assertEqual(calls[0].args, ('OLD', 0))
        self.assertEqual(len(calls), 4)
        self.assertGreaterEqual(self.context.portfolio.available_cash, 0)
        self.assertLessEqual(sum(p.value for p in self.context.portfolio.positions.values()),
                             95000)

    def test_empty_targets_exit_even_small_positions(self):
        self.hold('OLD', 1000)
        self.adapter.execute_etf_targets(self.context, {})
        self.api.order_target_value.assert_called_once_with('OLD', 0)

    def test_unfilled_reduction_defers_buys(self):
        self.hold('OLD', 40000)
        self.api.order_target_value.side_effect = None
        self.api.order_target_value.return_value = SimpleNamespace(filled=50, amount=100)
        self.adapter.execute_etf_targets(self.context, {'A': 0.4})
        self.api.order_target_value.assert_called_once_with('OLD', 0)

    def test_paused_limit_down_and_t1_sales_defer_buys(self):
        for reason in ('paused', 'limit_down', 't1', 'partial_t1'):
            with self.subTest(reason=reason):
                self.context.portfolio.positions = {}
                self.context.portfolio.available_cash = 100000
                self.hold('OLD', 40000, closeable=0 if reason == 't1' else 1000
                          if reason == 'partial_t1' else None)
                snapshot = self.api.get_current_data.return_value['OLD']
                snapshot.paused = reason == 'paused'
                snapshot.last_price = 9 if reason == 'limit_down' else 10
                self.api.order_target_value.reset_mock()
                self.adapter.execute_etf_targets(self.context, {'A': 0.4})
                self.api.order_target_value.assert_not_called()

    def test_paused_and_limit_up_buys_are_skipped(self):
        self.api.get_current_data.return_value['A'].paused = True
        self.api.get_current_data.return_value['B'].last_price = 11
        self.adapter.execute_etf_targets(self.context, {'A': 0.4, 'B': 0.3})
        self.api.order_target_value.assert_not_called()

    def test_open_orders_prevent_duplicate_submission(self):
        self.api.get_open_orders.return_value = {'pending': object()}
        self.adapter.execute_etf_targets(self.context, {'A': 0.4})
        self.api.order_target_value.assert_not_called()

    def test_bad_weights_raise_without_orders(self):
        for weights in ({'A': -0.1}, {'A': float('nan')}, {'A': 0.5},
                        {'A': 0.4, 'B': 0.4, 'C': 0.4}):
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                self.adapter.execute_etf_targets(self.context, weights)
        self.api.order_target_value.assert_not_called()

    def test_small_changes_and_insufficient_lot_are_skipped(self):
        self.hold('A', 39000)
        self.adapter.execute_etf_targets(self.context, {'A': 0.4})
        self.api.order_target_value.assert_not_called()
        self.context.portfolio.total_value = 1000
        self.context.portfolio.positions = {}
        self.context.portfolio.available_cash = 1000
        self.adapter.execute_etf_targets(self.context, {'A': 0.4})
        self.api.order_target_value.assert_not_called()

    def test_failed_buy_stops_subsequent_buys(self):
        self.api.order_target_value.side_effect = None
        self.api.order_target_value.return_value = None
        self.adapter.execute_etf_targets(self.context, {'A': 0.4, 'B': 0.3})
        self.assertEqual(self.api.order_target_value.call_count, 1)

    def test_all_missing_data_does_not_trigger_liquidation(self):
        self.adapter.initialize(self.context)
        self.api.get_security_info.return_value = None
        with self.assertRaisesRegex(ValueError, 'No usable ETF histories'):
            self.adapter.rebalance_etfs(self.context)
        self.api.order_target_value.assert_not_called()

    def test_price_requests_end_on_previous_date_and_feed_same_core(self):
        self.adapter.initialize(self.context)
        self.api.g.etf_universe = ['A']
        self.api.get_security_info.return_value = SimpleNamespace(start_date=date(2020, 1, 1))
        bars = trending_history()
        self.context.previous_date = bars[-1].date

        class Column:
            @property
            def iloc(self):
                return self

            def __getitem__(self, key):
                return [30000000.0] * 20

        class Frame:
            def __len__(self):
                return len(bars)

            def __getitem__(self, key):
                return Column()

            def iterrows(self):
                for bar in bars:
                    yield datetime.combine(bar.date, datetime.min.time()), {
                        'close': bar.close, 'high': bar.high, 'low': bar.low,
                        'volume': bar.volume,
                    }

        self.api.get_price.return_value = Frame()
        self.adapter.rebalance_etfs(self.context)
        kwargs = self.api.get_price.call_args.kwargs
        self.assertEqual(kwargs['end_date'], self.context.previous_date)
        self.assertFalse(kwargs['skip_paused'])
        expected = build_rotation_targets({'A': bars}, bars[-1].date)
        self.api.record.assert_called_once_with(target_exposure=0.4, target_cash=0.6)
        self.assertAlmostEqual(self.api.order_target_value.call_args.args[1],
                               expected['weights']['A'] * 100000 * 0.995)


class StrategyExportTests(unittest.TestCase):
    def test_combined_strategy_is_standalone_and_python38_parseable(self):
        root = Path(etf_rotation.__file__).parent
        core = (root / 'etf_rotation.py').read_text(encoding='utf-8')
        adapter = (root / 'platforms' / 'joinquant_etf_rotation.py').read_text(encoding='utf-8')
        local_import = 'from strategies.etf_rotation import RotationBar, RotationConfig, build_rotation_targets\n'
        self.assertEqual(adapter.count(local_import), 1)
        combined = core + '\n\n' + adapter.replace(local_import, '')
        ast.parse(combined, feature_version=(3, 8))
        self.assertNotIn('from stockmarket', combined)
        self.assertIn('from jqdata import *', combined)


if __name__ == '__main__':
    unittest.main()
