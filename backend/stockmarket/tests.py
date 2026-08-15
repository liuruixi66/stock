from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from market_data import HistoricalBar, Market, Quote
from .models import SimulationAccount, SimulationPosition
from .paper_trading import TradingError, submit_order
from .quant_research import run_sma_cross


class FakeProvider:
    def get_quote(self, symbol: str) -> Quote:
        return Quote(
            symbol=symbol,
            market=Market.A_SHARE,
            name='测试股票',
            price=10,
            previous_close=9.5,
            open=9.6,
            high=10.2,
            low=9.4,
            volume=100000,
            currency='CNY',
            timestamp=__import__('datetime').datetime.now(__import__('datetime').timezone.utc),
            source='test',
        )


class PaperTradingTests(TestCase):
    def setUp(self) -> None:
        self.account = SimulationAccount.objects.create(
            name='A股研究账户',
            market='A',
            currency='CNY',
            initial_cash=Decimal('100000'),
            cash=Decimal('100000'),
        )

    @patch('stockmarket.paper_trading.get_provider', return_value=FakeProvider())
    def test_market_buy_creates_position_and_reduces_cash(self, _provider) -> None:
        order = submit_order(self.account.id, '000001', 'BUY', 100)

        self.account.refresh_from_db()
        position = SimulationPosition.objects.get(account=self.account, symbol='000001')
        self.assertEqual(order.status, 'FILLED')
        self.assertEqual(position.quantity, 100)
        self.assertLess(self.account.cash, Decimal('99000'))

    def test_a_share_buy_quantity_requires_board_lot(self) -> None:
        with self.assertRaises(TradingError):
            submit_order(self.account.id, '000001', 'BUY', 1)


class QuantResearchTests(TestCase):
    def test_sma_cross_returns_metrics_and_trades(self) -> None:
        start = date(2025, 1, 1)
        prices = [10, 10, 10, 11, 12, 13, 12, 11, 10, 9, 10, 11, 12]
        bars = [HistoricalBar(
            date=start + timedelta(days=index),
            open=price,
            high=price,
            low=price,
            close=price,
            volume=1000,
        ) for index, price in enumerate(prices)]

        result = run_sma_cross(bars, 100000, short_window=2, long_window=3)

        self.assertEqual(result['strategy'], 'sma_cross')
        self.assertGreaterEqual(result['trade_count'], 2)
        self.assertEqual(len(result['equity_curve']), len(bars))