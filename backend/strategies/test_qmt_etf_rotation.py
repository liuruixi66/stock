import unittest
from unittest.mock import patch

from strategies.qmt_etf_rotation import (
    ETF_UNIVERSE,
    EQUITY_ETFS,
    DEFENSIVE_ETFS,
    MAX_PEAK_DRAWDOWN,
    MAX_TOTAL_EXPOSURE,
    EQUITY_RISK_OFF_COOLDOWN,
    MODEL_TYPE,
    FRACTIONAL_HISTORY_COUNT,
    FORECAST_HORIZON,
    REBALANCE_INTERVAL,
    RISK_OFF_COOLDOWN,
    analyze_benchmark,
    build_targets,
    difference_forecast,
    fractional_weights,
    handlebar,
    init,
    score_history,
    lstm_dataset,
    lstm_forecast,
    lstm_device,
    forecast_history_count,
    isolated_lstm_batch,
    close_lstm_worker,
    execution_open_prices,
    audit_missing_bars,
    suspension_valuation,
    reserve_suspended_targets,
    _execute_targets,
)


def rising_history(daily_return):
    values = [100.0]
    for _ in range(121):
        values.append(values[-1] * (1 + daily_return))
    return values


class FakeContext:
    do_back_test = 1
    barpos = 122
    capital = 1000000

    def set_universe(self, universe):
        self.universe = universe

    def get_history_data(self, count, period, field):
        if hasattr(self, 'histories'):
            return self.histories
        return {symbol: rising_history(0.003) for symbol in ETF_UNIVERSE}

    def get_bar_timetag(self, bar):
        from datetime import datetime, timezone
        return int(datetime(2017, 8, 30, tzinfo=timezone.utc).timestamp() * 1000)

    def get_market_data_ex(self, **kwargs):
        import pandas as pd
        histories = self.get_history_data(1, '1d', 'open')
        return {symbol: pd.DataFrame({'open': [values[-1]]}, index=['20170830'])
                for symbol, values in histories.items()}


class QmtEtfRotationTests(unittest.TestCase):
    def setUp(self):
        self.model_patch = patch('strategies.qmt_etf_rotation.MODEL_TYPE', 'fractional')
        self.model_patch.start()
        self.addCleanup(self.model_patch.stop)
        self.history_patch = patch(
            'strategies.qmt_etf_rotation.FRACTIONAL_HISTORY_COUNT', 122)
        self.history_patch.start()
        self.addCleanup(self.history_patch.stop)

    def test_signal_uses_only_completed_bars(self):
        closes = rising_history(0.003)
        first = score_history(closes)
        self.assertIsNotNone(first)
        closes[-1] = 1000000.0
        second = score_history(closes)
        self.assertEqual(first, second)

    def test_fractional_weights_match_research(self):
        from research.fractional_forecast import fractional_weights as research_weights
        for order in (0.0, 0.25, 0.5, 0.75, 1.0):
            self.assertEqual(fractional_weights(order).tolist(),
                             research_weights(order).tolist())

    def test_forecast_reconstructs_known_return_without_current_bar(self):
        closes = rising_history(0.003)
        result = difference_forecast(closes)
        self.assertTrue(result['validation_passed'])
        self.assertLess(result['last_training_target_index'],
                        result['first_validation_origin_index'])
        self.assertAlmostEqual(result['predicted_return'],
                               (1.003 ** FORECAST_HORIZON) - 1, delta=0.0002)
        closes[-1] *= 100
        self.assertEqual(result, difference_forecast(closes))

    def test_failed_validation_cannot_generate_buy_signal(self):
        with patch('strategies.qmt_etf_rotation.difference_forecast', return_value={
                'validation_passed': False, 'predicted_return': 0.05}):
            self.assertIsNone(score_history(rising_history(0.003)))

    def test_targets_are_bounded_and_only_use_fixed_universe(self):
        histories = {
            symbol: rising_history(0.001 + index * 0.0002)
            for index, symbol in enumerate(ETF_UNIVERSE)
        }
        targets = build_targets(histories)
        self.assertLessEqual(sum(targets['weights'].values()), MAX_TOTAL_EXPOSURE)
        self.assertLessEqual(len(targets['selected']), 3)
        self.assertEqual(set(targets['weights']), set(ETF_UNIVERSE))
        self.assertAlmostEqual(
            targets['cash_weight'], 1 - sum(targets['weights'].values()),
        )

    def test_no_positive_trend_stays_in_cash(self):
        histories = {symbol: rising_history(-0.001) for symbol in ETF_UNIVERSE}
        targets = build_targets(histories)
        self.assertEqual(targets['selected'], [])
        self.assertEqual(targets['cash_weight'], 1.0)

    def test_short_history_is_not_selected(self):
        self.assertIsNone(score_history([100.0] * 121))

    def test_benchmark_stress_and_recovery_detection(self):
        calm = analyze_benchmark(rising_history(0.001))
        self.assertFalse(calm['stress'])
        self.assertTrue(calm['recovered'])

        shocked = rising_history(0.001)
        shocked[-2] = shocked[-3] * 0.94
        stress = analyze_benchmark(shocked)
        self.assertTrue(stress['stress'])
        self.assertIn('benchmark_daily_shock', stress['reason'])

    def test_strategy_refuses_live_mode(self):
        context = FakeContext()
        context.do_back_test = 0
        with self.assertRaisesRegex(RuntimeError, 'backtest-only'):
            init(context)

    def test_market_shock_triggers_cash_exit(self):
        context = FakeContext()
        context.histories = {
            symbol: rising_history(0.001) for symbol in ETF_UNIVERSE
        }
        benchmark = context.histories['510300.SH']
        benchmark[-2] = benchmark[-3] * 0.94
        position = type('Position', (), {
            'm_strInstrumentID': '510300',
            'm_strExchangeID': 'SH',
            'm_nVolume': 1000,
        })()
        submitted = []

        def fake_account_data(account_id, account_type, data_type):
            if data_type == 'ACCOUNT':
                account = type('Account', (), {
                    'm_dBalance': 1000000.0,
                    'm_dAvailable': 500000.0,
                })()
                return [account]
            return [position] if data_type == 'POSITION' else []

        init(context)
        with patch(
                'strategies.qmt_etf_rotation.get_trade_detail_data',
                side_effect=fake_account_data, create=True), patch(
                'strategies.qmt_etf_rotation.order_shares',
                side_effect=lambda *args: submitted.append(args) or 1,
                create=True):
            handlebar(context)

        self.assertEqual(
            context.risk_off_until, context.barpos + EQUITY_RISK_OFF_COOLDOWN)
        self.assertEqual([(order[0], order[1]) for order in submitted], [
            ('510300.SH', -1000),
        ])

    def test_reentry_requires_recovery_after_cooldown(self):
        context = FakeContext()
        submitted = []

        def fake_account_data(account_id, account_type, data_type):
            if data_type == 'ACCOUNT':
                account = type('Account', (), {
                    'm_dBalance': 1000000.0,
                    'm_dAvailable': 1000000.0,
                })()
                return [account]
            return []

        init(context)
        context.risk_off_until = (
            context.barpos - EQUITY_RISK_OFF_COOLDOWN - 1)
        context.rotation_last_bar = context.barpos - 1
        with patch(
                'strategies.qmt_etf_rotation.get_trade_detail_data',
                side_effect=fake_account_data, create=True), patch(
                'strategies.qmt_etf_rotation.order_shares',
                side_effect=lambda *args: submitted.append(args) or 1,
                create=True):
            handlebar(context)

        self.assertEqual(context.risk_off_until, -1)
        self.assertEqual(len(submitted), 3)

    def test_portfolio_drawdown_triggers_cash_exit(self):
        context = FakeContext()
        position = type('Position', (), {
            'm_strInstrumentID': '510300',
            'm_strExchangeID': 'SH',
            'm_nVolume': 1000,
        })()
        submitted = []

        def fake_account_data(account_id, account_type, data_type):
            if data_type == 'ACCOUNT':
                account = type('Account', (), {
                    'm_dBalance': 1000000.0 * (1 - MAX_PEAK_DRAWDOWN - 0.01),
                    'm_dAvailable': 500000.0,
                })()
                return [account]
            return [position] if data_type == 'POSITION' else []

        init(context)
        with patch(
                'strategies.qmt_etf_rotation.get_trade_detail_data',
                side_effect=fake_account_data, create=True), patch(
                'strategies.qmt_etf_rotation.order_shares',
                side_effect=lambda *args: submitted.append(args) or 1,
                create=True):
            handlebar(context)

        self.assertEqual(context.portfolio_off_until, context.barpos + RISK_OFF_COOLDOWN)
        self.assertEqual(context.peak_balance, context.capital)
        self.assertEqual([(order[0], order[1]) for order in submitted], [
            ('510300.SH', -1000),
        ])

    def test_defensive_assets_remain_eligible_when_equities_blocked(self):
        histories = {symbol: rising_history(0.001) for symbol in ETF_UNIVERSE}
        result = build_targets(histories, equity_blocked=True)
        self.assertIn('511010.SH', result['selected'])
        self.assertIn('511880.SH', result['selected'])
        for symbol in EQUITY_ETFS:
            self.assertEqual(result['weights'][symbol], 0)

    def test_expanded_pool_is_unique_and_risk_classified(self):
        self.assertEqual(len(ETF_UNIVERSE), 10)
        self.assertEqual(len(set(ETF_UNIVERSE)), 10)
        self.assertFalse(set(EQUITY_ETFS) & set(DEFENSIVE_ETFS))
        for symbol in ('510050.SH', '510880.SH', '512890.SH'):
            self.assertIn(symbol, EQUITY_ETFS)

    def test_new_assets_need_history_and_cannot_bypass_equity_risk(self):
        histories = {symbol: rising_history(0.003) for symbol in ETF_UNIVERSE}
        histories['512890.SH'] = [100.0] * 10
        result = build_targets(histories)
        self.assertIn('512890.SH', result['rejected'])
        self.assertEqual(result['weights']['512890.SH'], 0)
        blocked = build_targets(histories, equity_blocked=True)
        self.assertTrue(all(blocked['weights'][symbol] == 0 for symbol in EQUITY_ETFS))

    def test_minimum_commission_filters_small_defensive_budget(self):
        histories = {symbol: rising_history(0.0001) for symbol in ETF_UNIVERSE}
        self.assertIn('511010.SH', build_targets(histories)['selected'])
        self.assertNotIn('511010.SH', build_targets(histories, balance=1000)['selected'])

    def test_rank_buffer_keeps_close_incumbent(self):
        def feature(closes, symbol, cost):
            return {'score': {'510300.SH': 1.0, '510500.SH': 1.05,
                              '159915.SZ': 1.2, '588000.SH': 1.3}.get(symbol, 0.01)}
        histories = {symbol: rising_history(0.001) for symbol in ETF_UNIVERSE}
        with patch('strategies.qmt_etf_rotation.score_history', side_effect=feature):
            result = build_targets(histories, held=['510300.SH'])
        self.assertIn('510300.SH', result['selected'])
        self.assertNotIn('510500.SH', result['selected'])

    def test_normal_rebalance_skips_intervening_days(self):
        context = FakeContext()
        init(context)
        context.rotation_last_bar = context.barpos - REBALANCE_INTERVAL + 1
        account = type('Account', (), {
            'm_dBalance': 1000000.0, 'm_dAvailable': 1000000.0,
        })()
        with patch('strategies.qmt_etf_rotation.get_trade_detail_data',
                   side_effect=lambda a, t, d: [account] if d == 'ACCOUNT' else [],
                   create=True), patch('strategies.qmt_etf_rotation.order_shares',
                                      create=True) as submit:
            handlebar(context)
        submit.assert_not_called()

    def test_unfilled_reductions_block_new_buys(self):
        from strategies.qmt_etf_rotation import _execute_targets

        context = FakeContext()
        init(context)
        position = type('Position', (), {
            'm_strInstrumentID': '510300', 'm_strExchangeID': 'SH', 'm_nVolume': 1000,
        })()
        account = type('Account', (), {
            'm_dBalance': 1000000.0, 'm_dAvailable': 500000.0,
        })()
        weights = {symbol: 0.0 for symbol in ETF_UNIVERSE}
        weights['518880.SH'] = 0.3
        targets = {'weights': weights, 'selected': ['518880.SH']}
        prices = {symbol: 10.0 for symbol in ETF_UNIVERSE}
        with patch('strategies.qmt_etf_rotation.get_trade_detail_data',
                   side_effect=lambda a, t, d: [account] if d == 'ACCOUNT' else [position],
                   create=True), patch('strategies.qmt_etf_rotation.order_shares',
                                      create=True) as submit:
            _execute_targets(context, targets, {'510300.SH': 1000}, prices, 1000000.0)
        self.assertEqual(submit.call_count, 1)
        self.assertEqual(submit.call_args.args[1], -1000)

    def test_equity_cooldown_does_not_extend_on_persistent_bear_trend(self):
        context = FakeContext()
        init(context)
        context.risk_off_until = context.barpos - 1
        context.histories = {symbol: rising_history(-0.001) for symbol in ETF_UNIVERSE}
        account = type('Account', (), {
            'm_dBalance': 1000000.0, 'm_dAvailable': 1000000.0,
        })()
        original_deadline = context.risk_off_until
        with patch('strategies.qmt_etf_rotation.get_trade_detail_data',
                   side_effect=lambda a, t, d: [account] if d == 'ACCOUNT' else [],
                   create=True), patch('strategies.qmt_etf_rotation.order_shares',
                                      create=True):
            handlebar(context)
        self.assertEqual(context.risk_off_until, original_deadline)
        self.assertEqual(context.peak_balance, context.capital)

    def test_equity_and_portfolio_cooldowns_are_independent(self):
        self.assertEqual(EQUITY_RISK_OFF_COOLDOWN, 5)
        self.assertEqual(RISK_OFF_COOLDOWN, 20)

    def test_backtest_submits_only_bounded_etf_lot_orders(self):
        context = FakeContext()
        submitted = []

        def fake_account_data(account_id, account_type, data_type):
            if data_type == 'ACCOUNT':
                account = type('Account', (), {
                    'm_dBalance': 1000000.0,
                    'm_dAvailable': 1000000.0,
                })()
                return [account]
            return []

        init(context)
        with patch(
                'strategies.qmt_etf_rotation.get_trade_detail_data',
                side_effect=fake_account_data, create=True), patch(
                'strategies.qmt_etf_rotation.order_shares',
                side_effect=lambda *args: submitted.append(args) or 1,
                create=True):
            handlebar(context)

        self.assertEqual(len(submitted), 3)
        total_value = sum(order[1] * order[3] for order in submitted)
        self.assertLessEqual(total_value, 1000000.0 * MAX_TOTAL_EXPOSURE)
        for order in submitted:
            self.assertIn(order[0], ETF_UNIVERSE)
            self.assertGreater(order[1], 0)
            self.assertEqual(order[1] % 100, 0)


class QmtExecutionPriceTests(unittest.TestCase):
    def test_broker_audit_distinguishes_present_date_without_using_price(self):
        import pandas as pd
        context = FakeContext()
        data = {'159915.SZ': pd.DataFrame(
            {'open': [3.0, 3.1], 'close': [3.05, 3.2], 'volume': [1000, 1200]},
            index=['20210205', '20210208'])}
        with patch.object(context, 'get_market_data_ex', return_value=data) as query:
            report = audit_missing_bars(context, ['159915.SZ'], '20210208')
        self.assertIn('date_present', report['159915.SZ']['status'])
        self.assertEqual(query.call_args.kwargs['end_time'], '20210208235959')
        self.assertFalse(query.call_args.kwargs['fill_data'])
        self.assertFalse(query.call_args.kwargs['subscribe'])

    def test_broker_audit_does_not_infer_source_gap_or_use_future(self):
        import pandas as pd
        context = FakeContext()
        data = {'159915.SZ': pd.DataFrame(
            {'open': [3.0], 'close': [3.05], 'volume': [1000]}, index=['20210205'])}
        with patch.object(context, 'get_market_data_ex', return_value=data):
            report = audit_missing_bars(context, ['159915.SZ'], '20210208')
            self.assertIn('not_proof', report['159915.SZ']['status'])
        data['159915.SZ'].index = ['20210209']
        with patch.object(context, 'get_market_data_ex', return_value=data):
            with self.assertRaisesRegex(RuntimeError, 'future'):
                audit_missing_bars(context, ['159915.SZ'], '20210208')

    def test_exact_date_raw_open_replaces_legacy_out_of_range_price(self):
        import pandas as pd
        context = FakeContext()
        frame = pd.DataFrame({'open': [106.8]}, index=['20170830'])
        with patch.object(context, 'get_market_data_ex',
                          return_value={'511010.SH': frame}) as query:
            prices = execution_open_prices(context)
        self.assertEqual(prices['511010.SH'], 106.8)
        query.assert_any_call(
            fields=['open'], stock_code=list(ETF_UNIVERSE), period='1d',
            start_time='20170830', end_time='20170830235959', count=-1,
            dividend_type='none', fill_data=False, subscribe=False)
        query.assert_any_call(
            fields=['open'], stock_code=list(ETF_UNIVERSE), period='1d',
            start_time='20170830', end_time='20170830235959', count=-1,
            dividend_type='follow', fill_data=False, subscribe=False)
        self.assertNotEqual(prices['511010.SH'], 109.962)

    def test_stale_bar_stops_instead_of_clamping(self):
        import pandas as pd
        context = FakeContext()
        frame = pd.DataFrame({'open': [109.962]}, index=['20170829'])
        with patch.object(context, 'get_market_data_ex',
                          return_value={'511010.SH': frame}):
            with self.assertRaisesRegex(RuntimeError, 'date mismatch'):
                execution_open_prices(context)

    def test_adjusted_chart_stops_before_automatic_repricing(self):
        import pandas as pd
        context = FakeContext()
        raw = {'511880.SH': pd.DataFrame({'open': [100.97]}, index=['20170412'])}
        adjusted = {'511880.SH': pd.DataFrame({'open': [82.8971]}, index=['20170412'])}
        from datetime import datetime, timezone
        timestamp = int(datetime(2017, 4, 12, tzinfo=timezone.utc).timestamp() * 1000)
        with patch.object(context, 'get_bar_timetag', return_value=timestamp), patch.object(
                context, 'get_market_data_ex', side_effect=[raw, adjusted]):
            with self.assertRaisesRegex(RuntimeError, 'PRICE_BASIS_MISMATCH'):
                execution_open_prices(context)

    def test_missing_bar_does_not_reuse_previous_open(self):
        context = FakeContext()
        with patch.object(context, 'get_market_data_ex', return_value={}):
            self.assertEqual(execution_open_prices(context), {})

    def test_daily_chart_required(self):
        context = FakeContext()
        context.period = '1m'
        with self.assertRaisesRegex(RuntimeError, 'daily'):
            execution_open_prices(context)

    def test_duplicate_or_invalid_open_is_rejected(self):
        import pandas as pd
        context = FakeContext()
        for frame in (
                pd.DataFrame({'open': [106.8, 106.9]}, index=['20170830', '20170830']),
                pd.DataFrame({'open': [float('nan')]}, index=['20170830'])):
            with patch.object(context, 'get_market_data_ex',
                              return_value={'511010.SH': frame}):
                with self.assertRaises(RuntimeError):
                    execution_open_prices(context)


class QmtExecutionToleranceTests(unittest.TestCase):
    def targets(self, gold_weight=0.2):
        weights = {symbol: 0.0 for symbol in ETF_UNIVERSE}
        weights['511010.SH'] = 0.2
        weights['518880.SH'] = gold_weight
        return {'weights': weights, 'selected': ['511010.SH', '518880.SH']}

    def execute(self, targets, initial, confirmed, cash=790000):
        context = FakeContext()
        prices = {'511010.SH': 100.0, '518880.SH': 10.0, '510300.SH': 10.0}
        with patch('strategies.qmt_etf_rotation._account_snapshot',
                   return_value=(1000000, cash)), patch(
                'strategies.qmt_etf_rotation._positions', return_value=confirmed), patch(
                'strategies.qmt_etf_rotation._submit') as submit:
            _execute_targets(context, targets, initial, prices, 1000000)
        return context, submit

    def test_ignored_small_reduction_allows_other_buys(self):
        targets = self.targets()
        context, submit = self.execute(
            targets, {'511010.SH': 2100}, {'511010.SH': 2100})
        submit.assert_called_once_with(context, '518880.SH', 20000, 10.0)
        self.assertEqual(targets['weights']['511010.SH'], 0.2)

    def test_retained_exposure_and_cash_limit_new_buys(self):
        for cash, expected_shares in ((680000, 28000), (50000, 4900)):
            with self.subTest(cash=cash):
                targets = self.targets(gold_weight=0.3)
                targets['weights']['510300.SH'] = 0.1
                targets['selected'].append('510300.SH')
                positions = {'511010.SH': 2100, '510300.SH': 11000}
                context, submit = self.execute(
                    targets, positions, positions, cash)
                submit.assert_called_once_with(
                    context, '518880.SH', expected_shares, 10.0)

    def test_submitted_reduction_still_blocks_until_target_is_confirmed(self):
        for confirmed_shares in (2300, 2200, 2100):
            with self.subTest(confirmed_shares=confirmed_shares):
                context, submit = self.execute(
                    self.targets(), {'511010.SH': 2300},
                    {'511010.SH': confirmed_shares})
                submit.assert_called_once_with(context, '511010.SH', -300, 100.0)

    def test_completed_reduction_allows_other_buys(self):
        context, submit = self.execute(
            self.targets(), {'511010.SH': 2300}, {'511010.SH': 2000})
        self.assertEqual(submit.call_args_list, [
            unittest.mock.call(context, '511010.SH', -300, 100.0),
            unittest.mock.call(context, '518880.SH', 20000, 10.0),
        ])

    def test_small_full_exit_is_never_ignored(self):
        targets = self.targets()
        targets['weights']['511010.SH'] = 0.0
        targets['selected'] = ['518880.SH']
        for confirmed in ({'511010.SH': 100}, {}):
            with self.subTest(confirmed=confirmed):
                context, submit = self.execute(
                    targets, {'511010.SH': 100}, confirmed)
                self.assertEqual(submit.call_args_list[0],
                                 unittest.mock.call(context, '511010.SH', -100, 100.0))
                self.assertEqual(submit.call_count, 1 if confirmed else 2)

    def test_unexpected_increase_in_retained_position_blocks_buys(self):
        _, submit = self.execute(
            self.targets(), {'511010.SH': 2100}, {'511010.SH': 2200})
        submit.assert_not_called()


class QmtSuspensionTests(unittest.TestCase):
    def targets(self):
        return {'weights': {symbol: 0.3 if symbol in ('510300.SH', '511010.SH') else 0.0
                            for symbol in ETF_UNIVERSE},
                'selected': ['510300.SH', '511010.SH'], 'cash_weight': 0.4}

    def test_verified_suspension_uses_prior_close_only_for_sizing(self):
        reports = {'159915.SZ': {'rows': [
            {'date': '20210205', 'close': 3.084},
            {'date': '20210204', 'close': 3.098},
        ]}}
        self.assertEqual(suspension_valuation({'159915.SZ': 1000}, reports, '20210208'),
                         {'159915.SZ': 3.084})
        with self.assertRaisesRegex(RuntimeError, 'Unverified'):
            suspension_valuation({'159915.SZ': 1000}, reports, '20210209')
        reports['159915.SZ']['rows'].append({'date': '20210208', 'close': 3.1})
        with self.assertRaisesRegex(RuntimeError, 'conflicts'):
            suspension_valuation({'159915.SZ': 1000}, reports, '20210208')

    def test_frozen_exposure_reduces_targets_and_over_limit_blocks_buys(self):
        for shares, price, expected in ((1000, 300.0, 0.3), (1000, 700.0, 0.0)):
            targets = reserve_suspended_targets(
                self.targets(), {'159915.SZ': shares}, {'159915.SZ': price}, 1000000)
            tradable = sum(targets['weights'][symbol] for symbol in ('510300.SH', '511010.SH'))
            self.assertAlmostEqual(tradable, expected)
            if expected == 0:
                self.assertEqual(targets['selected'], [])

    def test_frozen_position_does_not_block_other_orders_or_become_fill_price(self):
        positions = {'159915.SZ': 100000}
        frozen = {'159915.SZ': 3.0}
        targets = reserve_suspended_targets(self.targets(), positions, frozen, 1000000)
        with patch('strategies.qmt_etf_rotation._account_snapshot',
                   return_value=(1000000, 700000)), patch(
                'strategies.qmt_etf_rotation._positions', return_value=positions), patch(
                'strategies.qmt_etf_rotation._submit') as submit:
            _execute_targets(FakeContext(), targets, positions,
                             {'510300.SH': 10.0, '511010.SH': 100.0}, 1000000, frozen)
        self.assertEqual(submit.call_count, 2)
        self.assertTrue(all(call.args[1] != '159915.SZ' for call in submit.call_args_list))
        bought = sum(call.args[2] * call.args[3] for call in submit.call_args_list)
        self.assertLessEqual(bought + 300000, 600000)

    def test_risk_off_can_sell_tradable_holdings_but_not_suspended(self):
        positions = {'159915.SZ': 1000, '510300.SH': 1000}
        frozen = {'159915.SZ': 3.084}
        targets = self.targets()
        targets['weights'] = {symbol: 0.0 for symbol in ETF_UNIVERSE}
        targets['selected'] = []
        targets = reserve_suspended_targets(targets, positions, frozen, 1000000)
        with patch('strategies.qmt_etf_rotation._account_snapshot',
                   return_value=(1000000, 990000)), patch(
                'strategies.qmt_etf_rotation._positions', return_value={'159915.SZ': 1000}), patch(
                'strategies.qmt_etf_rotation._submit') as submit:
            _execute_targets(FakeContext(), targets, positions, {'510300.SH': 10.0},
                             1000000, frozen)
        submit.assert_called_once_with(unittest.mock.ANY, '510300.SH', -1000, 10.0)
        self.assertGreater(targets['weights']['159915.SZ'], 0)

    def test_callback_continues_on_verified_suspension(self):
        from datetime import datetime, timezone
        context = FakeContext()
        timestamp = int(datetime(2021, 2, 8, tzinfo=timezone.utc).timestamp() * 1000)
        positions = {'159915.SZ': 1000}
        report = {'159915.SZ': {'rows': [{'date': '20210205', 'close': 3.084}]}}
        prices = {symbol: 100.0 for symbol in ETF_UNIVERSE if symbol != '159915.SZ'}
        with patch('strategies.qmt_etf_rotation.MODEL_TYPE', 'fractional'):
            init(context)
            with patch.object(context, 'get_bar_timetag', return_value=timestamp), patch(
                    'strategies.qmt_etf_rotation.execution_open_prices', return_value=prices), patch(
                    'strategies.qmt_etf_rotation.audit_missing_bars', return_value=report), patch(
                    'strategies.qmt_etf_rotation._positions', return_value=positions), patch(
                    'strategies.qmt_etf_rotation._account_snapshot',
                    return_value=(1000000, 900000)), patch(
                    'strategies.qmt_etf_rotation._submit') as submit:
                handlebar(context)
        self.assertEqual(context.rotation_last_bar, context.barpos)
        self.assertGreater(submit.call_count, 0)
        self.assertTrue(all(call.args[1] != '159915.SZ' for call in submit.call_args_list))
        self.assertLessEqual(submit.call_count + len(positions), 3)


class QmtLstmTests(unittest.TestCase):
    def setUp(self):
        self.dual_patch = patch('strategies.qmt_etf_rotation.LSTM_DUAL_GPU', False)
        self.dual_patch.start()
        self.addCleanup(self.dual_patch.stop)
        self.addCleanup(close_lstm_worker)

    def history(self):
        import numpy as np
        return (100 * np.exp(np.arange(504) * 0.001)).tolist()

    def test_active_experiment_is_window_matched_fractional_control(self):
        self.assertEqual(MODEL_TYPE, 'fractional')
        self.assertEqual(FRACTIONAL_HISTORY_COUNT, 504)
        self.assertEqual(forecast_history_count(), 504)

    def test_dataset_purges_both_boundaries_and_has_no_current_close(self):
        import numpy as np
        closes = self.history()
        data = lstm_dataset(closes)
        origins = data['origins']
        self.assertLess(origins[data['train_end'] - 1] + FORECAST_HORIZON,
                        origins[data['selection_start']])
        self.assertLess(origins[data['selection_end'] - 1] + FORECAST_HORIZON,
                        origins[data['gate_start']])
        self.assertEqual(data['x'].shape[1:], (20, 1))
        closes[-1] = float('nan')
        second = lstm_dataset(closes)
        for key in ('x', 'y', 'actual', 'latest'):
            np.testing.assert_array_equal(data[key], second[key])

    def test_gate_prices_cannot_change_training_or_scaling(self):
        import numpy as np
        closes = self.history()
        first = lstm_dataset(closes)
        closes[-20:-1] = [price * 1.5 for price in closes[-20:-1]]
        second = lstm_dataset(closes)
        for key in ('x', 'y'):
            np.testing.assert_array_equal(first[key][:first['train_end']],
                                          second[key][:second['train_end']])
        self.assertEqual(first['target_mean'], second['target_mean'])
        self.assertEqual(first['target_scale'], second['target_scale'])

    def test_lstm_warmup_and_failed_gate_do_not_fall_back(self):
        with patch('strategies.qmt_etf_rotation.MODEL_TYPE', 'lstm'), patch(
                'strategies.qmt_etf_rotation.isolated_lstm_batch', return_value={
                    'device': 'cuda', 'forecasts': {'single': {
                        'validation_passed': False, 'predicted_return': 0.5}}}) as forecast:
            self.assertIsNone(score_history(rising_history(0.003)))
            forecast.assert_not_called()
            self.assertIsNone(score_history(self.history()))
            forecast.assert_called_once()
            self.assertIsNotNone(score_history(rising_history(0.003), '511010.SH'))

    def test_cuda_request_fails_explicitly(self):
        with patch('strategies.qmt_etf_rotation.LSTM_DEVICE', 'cuda'), patch(
                'torch.cuda.is_available', return_value=False):
            with self.assertRaisesRegex(RuntimeError, 'no CPU fallback'):
                lstm_device()

    def test_invalid_completed_history_is_rejected(self):
        closes = self.history()
        closes[-2] = 0
        with self.assertRaisesRegex(ValueError, 'finite positive'):
            lstm_dataset(closes)

    def test_window_matched_regression_control(self):
        with patch('strategies.qmt_etf_rotation.MODEL_TYPE', 'fractional'), patch(
                'strategies.qmt_etf_rotation.FRACTIONAL_HISTORY_COUNT', 504):
            self.assertEqual(forecast_history_count(), 504)
            self.assertIsNone(score_history(rising_history(0.003)))
            self.assertIsNotNone(score_history(self.history()))

    def test_lstm_callback_requests_long_history_and_bounds_orders(self):
        context = FakeContext()
        context.histories = {symbol: self.history() for symbol in ETF_UNIVERSE}
        account = type('Account', (), {
            'm_dBalance': 1000000.0, 'm_dAvailable': 1000000.0,
        })()
        with patch('strategies.qmt_etf_rotation.MODEL_TYPE', 'lstm'), patch(
                'strategies.qmt_etf_rotation.isolated_lstm_batch',
                side_effect=lambda histories: {'device': 'cuda', 'forecasts': {
                    symbol: {'validation_passed': True, 'predicted_return': 0.01}
                    for symbol in histories}}), patch(
                'strategies.qmt_etf_rotation.get_trade_detail_data',
                side_effect=lambda a, t, d: [account] if d == 'ACCOUNT' else [],
                create=True), patch('strategies.qmt_etf_rotation.order_shares',
                                   return_value=1, create=True) as orders, patch.object(
                context, 'get_history_data', wraps=context.get_history_data) as history:
            init(context)
            handlebar(context)
        history.assert_any_call(504, '1d', 'close')
        self.assertGreater(orders.call_count, 0)
        self.assertLessEqual(sum(call.args[1] * call.args[3]
                                 for call in orders.call_args_list),
                             account.m_dBalance * MAX_TOTAL_EXPOSURE)

    def test_worker_failure_and_invalid_output_stop_execution(self):
        import subprocess
        mode = patch('strategies.qmt_etf_rotation.LSTM_PERSISTENT_WORKER', False)
        mode.start()
        self.addCleanup(mode.stop)
        for output in (
                subprocess.CompletedProcess([], 1, '', 'c10.dll failed'),
                subprocess.CompletedProcess([], 0, 'not json', ''),
                subprocess.CompletedProcess([], 0, '{"device":"cpu","forecasts":{}}', '')):
            with patch('subprocess.run', return_value=output):
                with self.assertRaises(RuntimeError):
                    isolated_lstm_batch({})
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired([], 180)):
            with self.assertRaisesRegex(RuntimeError, 'no orders submitted'):
                isolated_lstm_batch({})

    def test_real_isolated_cuda_worker_without_parent_torch_import(self):
        import subprocess
        import sys
        code = (
            "import sys, io, contextlib; "
            "from strategies.qmt_etf_rotation import init; "
            "from strategies.test_qmt_etf_rotation import FakeContext; "
            "import strategies.qmt_etf_rotation as strategy; strategy.LSTM_DUAL_GPU=False; "
            "assert 'torch' not in sys.modules; "
            "context = FakeContext(); "
            "\nwith contextlib.redirect_stdout(io.StringIO()): init(context)\n"
            "assert 'torch' not in sys.modules; print('cuda')"
        )
        completed = subprocess.run([sys.executable, '-c', code],
                                   capture_output=True, text=True, timeout=60)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), 'cuda')
        with patch('strategies.qmt_etf_rotation.LSTM_EPOCHS', 2):
            batch = isolated_lstm_batch({'test': self.history()})
        self.assertTrue(batch['forecasts']['test']['validation_passed'])
        self.assertEqual(batch['device'], 'cuda')

    def test_persistent_dual_gpu_matches_independent_forecasts(self):
        import strategies.qmt_etf_rotation as strategy
        with patch('strategies.qmt_etf_rotation.LSTM_EPOCHS', 2):
            histories = {'first': self.history(), 'second': self.history()}
            single = isolated_lstm_batch(histories)
            close_lstm_worker()
            with patch('strategies.qmt_etf_rotation.LSTM_DUAL_GPU', True):
                dual = isolated_lstm_batch(histories)
                pids = {key: client.process.pid
                        for key, client in strategy._lstm_clients.items()}
                repeated = isolated_lstm_batch(histories)
                self.assertEqual(pids, {key: client.process.pid
                                       for key, client in strategy._lstm_clients.items()})
        self.assertEqual(set(pids), {'cuda:0', 'cuda:1'})
        self.assertNotEqual(pids['cuda:0'], pids['cuda:1'])
        self.assertEqual(dual, repeated)
        for symbol, forecast in dual['forecasts'].items():
            self.assertIn(forecast['device'], ('cuda:0', 'cuda:1'))
            for key in ('predicted_return', 'validation_mse', 'baseline_mse'):
                self.assertAlmostEqual(forecast[key], single['forecasts'][symbol][key],
                                       delta=1e-8)

    def test_persistent_timeout_stops_child(self):
        import strategies.qmt_etf_rotation as strategy
        isolated_lstm_batch({})
        client = strategy._lstm_clients['cuda']
        with patch.object(client, 'request', side_effect=RuntimeError('timed out')):
            with self.assertRaisesRegex(RuntimeError, 'no orders submitted'):
                isolated_lstm_batch({})
        self.assertIsNotNone(client.process.poll())
        self.assertNotIn('cuda', strategy._lstm_clients)

    def test_worker_client_needs_no_temp_directory_and_drains_stderr(self):
        import sys
        import os
        from strategies.qmt_etf_rotation import _LstmWorkerClient

        code = (
            "import sys; sys.stdin.readline(); "
            "sys.stderr.write('x' * 100000 + 'WORKER_ERROR_MARKER'); "
            "sys.stderr.flush(); sys.exit(1)"
        )
        with patch('tempfile.TemporaryFile', side_effect=OSError('No usable temporary directory')):
            client = _LstmWorkerClient([sys.executable, '-c', code], os.environ.copy(), os.getcwd())
            try:
                with self.assertRaisesRegex(RuntimeError, 'WORKER_ERROR_MARKER'):
                    client.request('{}')
                self.assertLessEqual(len(client.errors), 6000)
            finally:
                client.close()

    def test_missing_second_gpu_is_explicit(self):
        with patch('strategies.qmt_etf_rotation.LSTM_DEVICE', 'cuda:1'), patch(
                'torch.cuda.is_available', return_value=True), patch(
                'torch.cuda.device_count', return_value=1):
            with self.assertRaisesRegex(RuntimeError, 'device 1 unavailable'):
                lstm_device()

    def test_cuda_training_inference_and_repeatability(self):
        import torch
        if not torch.cuda.is_available():
            self.skipTest('CUDA hardware unavailable')
        with patch('strategies.qmt_etf_rotation.LSTM_DEVICE', 'cuda'), patch(
                'strategies.qmt_etf_rotation.LSTM_EPOCHS', 2):
            state = torch.random.get_rng_state().clone()
            first = lstm_forecast(self.history())
            second = lstm_forecast(self.history())
            self.assertTrue(torch.equal(state, torch.random.get_rng_state()))
        self.assertEqual(first, second)
        self.assertEqual(first['device'], 'cuda')
        self.assertTrue(first['validation_passed'])
        self.assertGreaterEqual(first['training_samples'], 100)
        self.assertGreaterEqual(first['selection_samples'], 30)
        self.assertGreaterEqual(first['validation_samples'], 30)
        self.assertAlmostEqual(first['predicted_return'], 1.0010005001667084 ** 5 - 1,
                               delta=0.0001)


if __name__ == '__main__':
    unittest.main()
