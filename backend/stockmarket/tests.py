from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from market_data import HistoricalBar, Market, Quote
from .analytics import build_account_analytics
from .models import SimulationAccount, SimulationOrder, SimulationPosition
from .paper_trading import TradingError, submit_order
from .quant_research import run_portfolio_baseline, run_sma_cross


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

    @patch('stockmarket.paper_trading.get_provider', return_value=FakeProvider())
    def test_crypto_order_allows_fractional_quantity(self, _provider) -> None:
        account = SimulationAccount.objects.create(
            name='虚拟货币研究账户',
            market='CRYPTO',
            currency='USDT',
            initial_cash=Decimal('100000'),
            cash=Decimal('100000'),
        )

        order = submit_order(account.id, 'BTCUSDT', 'BUY', Decimal('0.25'))

        position = SimulationPosition.objects.get(account=account, symbol='BTCUSDT')
        self.assertEqual(order.status, 'FILLED')
        self.assertEqual(position.quantity, Decimal('0.25'))


class MarketHistoryApiTests(TestCase):
    @patch('stockmarket.trading_views.get_provider')
    def test_history_endpoint_returns_normalized_remote_bars(self, get_provider_mock) -> None:
        class HistoryProvider:
            def get_history(self, symbol, start, end):
                return [HistoricalBar(
                    date=date(2025, 1, 2),
                    open=10,
                    high=11,
                    low=9,
                    close=10.5,
                    volume=1000,
                )]

        get_provider_mock.return_value = HistoryProvider()
        response = self.client.get(reverse('market_history'), {
            'market': 'US',
            'symbol': 'AAPL',
            'start_date': '2025-01-01',
            'end_date': '2025-01-31',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['bars'][0]['close'], 10.5)

    @patch('stockmarket.trading_views.get_provider')
    def test_portfolio_backtest_endpoint_runs_remote_baseline(self, get_provider_mock) -> None:
        class PortfolioProvider:
            def get_history(self, symbol, start, end):
                prices = [100, 101, 102, 103, 104, 105]
                return [HistoricalBar(
                    date=date(2025, 1, 1) + timedelta(days=index),
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    volume=1000,
                ) for index, price in enumerate(prices)]

        get_provider_mock.return_value = PortfolioProvider()
        response = self.client.post(
            reverse('portfolio_backtest'),
            data={
                'market': 'US',
                'symbols': ['AAPL', 'MSFT'],
                'strategy': 'equal_weight',
                'lookback': 1,
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['strategy'], 'equal_weight')
        self.assertEqual(response.json()['data']['data_counts']['AAPL'], 6)


class AnalyticsTests(TestCase):
    def setUp(self) -> None:
        self.account = SimulationAccount.objects.create(
            name='分析账户',
            market='A',
            currency='CNY',
            initial_cash=Decimal('100000'),
            cash=Decimal('100000'),
        )

    def _order(self, side: str, price: str, quantity: int, commission: str) -> None:
        SimulationOrder.objects.create(
            account=self.account,
            symbol='000001',
            side=side,
            order_type='MARKET',
            quantity=quantity,
            executed_price=Decimal(price),
            commission=Decimal(commission),
            status='FILLED',
        )

    @patch('stockmarket.analytics.get_provider', return_value=FakeProvider())
    def test_fifo_pairs_sells_against_earliest_buys(self, _provider) -> None:
        self._order('BUY', '10', 100, '3')
        self._order('BUY', '12', 100, '3')
        self._order('SELL', '14', 100, '4')

        result = build_account_analytics(self.account)
        sell = next(item for item in result['trades'] if item['side'] == 'SELL')

        # 卖出 14*100-4 = 1396，配对首笔买入成本 10*100+3 = 1003
        self.assertAlmostEqual(sell['realized_pnl'], 393.0, places=4)
        self.assertEqual(result['summary']['closed_count'], 1)
        self.assertEqual(result['summary']['win_rate'], 100.0)


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

    def test_portfolio_baselines_return_metrics_and_weights(self) -> None:
        start = date(2025, 1, 1)
        prices_a = [100, 101, 102, 101, 103, 104, 106, 105]
        prices_b = [100, 99, 98, 100, 99, 101, 100, 102]
        bars_by_symbol = {
            'AAA': [HistoricalBar(start + timedelta(days=index), price, price, price, price, 1000)
                    for index, price in enumerate(prices_a)],
            'BBB': [HistoricalBar(start + timedelta(days=index), price, price, price, price, 1000)
                    for index, price in enumerate(prices_b)],
        }

        for strategy in ('equal_weight', 'risk_parity', 'tsmom'):
            result = run_portfolio_baseline(
                bars_by_symbol,
                initial_cash=100000,
                strategy=strategy,
                lookback=2,
            )
            self.assertEqual(result['strategy'], strategy)
            self.assertEqual(len(result['equity_curve']), len(prices_a))
            self.assertIn('sharpe_ratio', result['metrics'])
            self.assertTrue(result['weight_history'])