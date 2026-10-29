from unittest import TestCase

from market_data.price_basis import adjusted_ohlc, research_price_contract


class PriceBasisTests(TestCase):
    def test_adjustment_is_identical_for_all_four_prices(self):
        self.assertEqual(adjusted_ohlc(10, 12, 9, 11, 5.5), (5, 6, 4.5, 5.5))

    def test_invalid_adjustments_are_not_silently_replaced(self):
        for adjusted_close in (None, float('nan'), float('inf'), 0, -1):
            with self.subTest(adjusted_close=adjusted_close), self.assertRaises(ValueError):
                adjusted_ohlc(10, 12, 9, 11, adjusted_close)

    def test_invalid_ohlc_and_overflow_are_rejected(self):
        for values in ((10, 9, 8, 11, 5), (10, 12, 11, 10, 5),
                       (1e308, 1e308, 1, 1, 1e308)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                adjusted_ohlc(*values)

    def test_constant_reanchoring_does_not_change_simple_returns(self):
        original = [5.0, 5.5, 5.25]
        reanchored = [price * 3.4 for price in original]
        for index in range(2):
            self.assertAlmostEqual(
                original[index + 1] / original[index] - 1,
                reanchored[index + 1] / reanchored[index] - 1,
            )

    def test_contract_is_fresh_and_explicitly_not_live_ready(self):
        contract = research_price_contract()
        self.assertIs(contract['live_trading_eligible'], False)
        self.assertIs(contract['point_in_time_verified'], False)
        contract['version'] = 'mutated'
        self.assertEqual(research_price_contract()['version'], 'fractional-price-policy-v1')
