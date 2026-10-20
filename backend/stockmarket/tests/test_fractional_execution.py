from datetime import date, timedelta

import pandas as pd
from django.test import SimpleTestCase

from research.fractional_execution import execution_fee, simulate_cash_shares
from research.fractional_forecast import DatabaseRandomUniverse, DifferencingError


class FractionalExecutionTests(SimpleTestCase):
    def setUp(self):
        self.start = date(2025, 1, 1)
        self.universe = DatabaseRandomUniverse(['600001.SH'], self.start, 43, 1)
        self.prices = pd.DataFrame([
            {
                'date': self.start + timedelta(days=i), 'instrument': '600001.SH',
                'open': 10.0, 'high': 10.0, 'low': 10.0, 'close': 10.0,
                'volume': 1000, 'dividends': 0.0, 'splits': 0.0,
            } for i in range(4)
        ])
        self.forecasts = {
            (self.start + timedelta(days=i), '600001.SH'): 0.1 for i in range(3)
        }

    def run_simulation(self, **kwargs):
        return simulate_cash_shares(
            self.prices, self.forecasts, self.universe,
            self.start, self.start + timedelta(days=3), exposure=1,
            initial_capital=kwargs.pop('initial_capital', 1005), **kwargs,
        )

    def test_minimum_commission_is_separate_from_sell_levy(self):
        self.assertEqual(execution_fee(1000, 0.0005, 5, 0), 5)
        self.assertEqual(execution_fee(1000, 0.0005, 5, 0.0005), 5.5)
        self.assertEqual(execution_fee(20000, 0.0005, 5, 0.0005), 20)
        self.assertEqual(execution_fee(0, 0.0005, 5, 0.0005), 0)

    def test_affordability_includes_minimum_fee_and_whole_lot(self):
        self.assertEqual(self.run_simulation(initial_capital=1000)['order_count'], 0)
        result = self.run_simulation(initial_capital=1005)
        self.assertEqual(result['order_count'], 1)
        self.assertEqual(result['trades'][0]['quantity'], 100)
        self.assertEqual(result['equity_curve'][-1]['cash'], 0)
        self.assertEqual(result['equity_curve'][-1]['equity'], 1000)

    def test_next_open_execution_and_settled_share_sales(self):
        self.forecasts[(self.start + timedelta(days=1), '600001.SH')] = -0.1
        self.forecasts[(self.start + timedelta(days=2), '600001.SH')] = -0.1
        result = self.run_simulation()
        buy, sell = result['trades']
        self.assertEqual(buy['date'], '2025-01-02')
        self.assertEqual(sell['date'], '2025-01-03')
        self.assertGreater(sell['date'], buy['date'])
        self.assertLessEqual(sell['quantity'], sell['sellable_before'])
        self.assertEqual(result['costs'], 10.5)
        self.assertEqual(result['equity_curve'][-1]['equity'], 994.5)

    def test_dividends_are_receivables_not_spendable_cash(self):
        self.prices.loc[1, 'dividends'] = 10
        self.prices.loc[2, 'dividends'] = 10
        result = self.run_simulation()
        self.assertEqual(result['order_count'], 1)
        self.assertEqual(result['dividend_receivables'], 1000)
        self.assertEqual(result['equity_curve'][1]['dividend_receivables'], 0)
        self.assertEqual(result['equity_curve'][-1]['cash'], 0)
        self.assertEqual(result['equity_curve'][-1]['equity'], 2000)

    def test_suspension_prevents_fills(self):
        self.prices.loc[1, 'volume'] = 0
        result = self.run_simulation()
        self.assertEqual(result['trades'][0]['date'], '2025-01-03')

    def test_split_and_non_cent_inputs_are_rejected(self):
        self.prices.loc[1, 'splits'] = 2
        with self.assertRaisesRegex(DifferencingError, 'splits'):
            self.run_simulation()
        self.prices.loc[1, 'splits'] = 0
        self.prices.loc[1, ['open', 'high', 'low', 'close']] = 10.001
        with self.assertRaisesRegex(DifferencingError, 'Non-cent'):
            self.run_simulation()

    def test_missing_action_and_forecast_data_are_explicit_errors(self):
        original = self.prices
        self.prices = self.prices.drop(columns=['dividends'])
        with self.assertRaisesRegex(DifferencingError, 'explicit action'):
            self.run_simulation()
        self.prices = original
        self.forecasts.clear()
        with self.assertRaisesRegex(DifferencingError, 'Missing replay forecast'):
            self.run_simulation()

    def test_missing_stock_day_is_rejected(self):
        self.prices.loc[1, 'instrument'] = '600002.SH'
        with self.assertRaisesRegex(DifferencingError, 'Missing or unexpected'):
            self.run_simulation()
