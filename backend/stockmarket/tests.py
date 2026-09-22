import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from market_data import HistoricalBar, Market, MarketDataError, MinuteBar, Quote
from market_data.local_history import LocalHistoryProvider, download_history
from .analytics import build_account_analytics
from .models import SimulationAccount, SimulationOrder, SimulationPosition
from .paper_trading import TradingError, submit_order
from .quant_research import reconstruct_differenced_forecast, run_leaky_integrator_experiment, run_portfolio_baseline, run_sma_cross


class LocalHistoryTests(SimpleTestCase):
    @patch('market_data.local_history.get_provider')
    def test_corrupted_snapshot_is_rejected(self, remote) -> None:
        remote.return_value.get_history.return_value = [
            HistoricalBar(date(2024, 1, 2), 10, 11, 9, 10.5, 1000),
        ]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            download_history('US', 'AAPL', date(2024, 1, 1), date(2024, 1, 3), root)
            local = LocalHistoryProvider('US', root)
            path = local.path('AAPL')
            payload = json.loads(path.read_text())
            payload['bars'][0]['close'] = 11
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(MarketDataError, 'integrity'):
                local.get_history('AAPL', date(2024, 1, 1), date(2024, 1, 3))

    @patch('market_data.local_history.get_provider')
    def test_download_command_keeps_successes_and_reports_failures(self, remote) -> None:
        def history(symbol, start, end):
            if symbol == 'MSFT':
                raise MarketDataError('Unavailable source')
            return [HistoricalBar(date(2024, 1, 2), 10, 11, 9, 10.5, 1000)]

        remote.return_value.get_history.side_effect = history
        with TemporaryDirectory() as directory:
            output = StringIO()
            with self.assertRaises(CommandError):
                call_command('download_history', '--market', 'US', '--symbols', 'AAPL', 'MSFT',
                             '--start', '2024-01-01', '--end', '2024-01-03', '--output', directory,
                             stdout=output, stderr=StringIO())
            self.assertIn('Completed: 1; failed: 1', output.getvalue())
            self.assertTrue((Path(directory) / 'US' / 'AAPL.json').exists())
            self.assertFalse((Path(directory) / 'US' / 'MSFT.json').exists())

    @patch('market_data.local_history.get_provider')
    def test_incomplete_crypto_history_is_rejected(self, remote) -> None:
        remote.return_value.get_history.return_value = [
            HistoricalBar(date(2024, 1, 2), 10, 11, 9, 10.5, 1000),
        ]
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(MarketDataError, 'Incomplete crypto'):
                download_history('CRYPTO', 'BTCUSDT', date(2024, 1, 1), date(2024, 1, 3), Path(directory))
            self.assertFalse(list(Path(directory).rglob('*.json')))

    @patch('market_data.local_history.get_provider')
    def test_download_then_read_offline_without_overwriting(self, remote) -> None:
        start, end = date(2024, 1, 1), date(2024, 1, 3)
        remote.return_value.get_history.return_value = [
            HistoricalBar(date(2024, 1, 2), 10, 11, 9, 10.5, 1000),
        ]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            metadata = download_history('US', 'aapl', start, end, root)
            self.assertEqual(metadata['bar_count'], 1)
            remote.reset_mock()
            remote.side_effect = AssertionError('Network is forbidden')
            local = LocalHistoryProvider('US', root)
            self.assertEqual(local.get_history('AAPL', start, end)[0].close, 10.5)
            self.assertTrue(download_history('US', 'AAPL', start, end, root)['cached'])
            with self.assertRaises(MarketDataError):
                local.get_history('MSFT', start, end)
            with self.assertRaises(MarketDataError):
                local.get_history('AAPL', start, end + timedelta(days=1))
            remote.assert_not_called()

    @patch('market_data.local_history.get_provider')
    def test_crypto_download_chunks_more_than_1000_days(self, remote) -> None:
        def history(symbol, start, end):
            return [HistoricalBar(start + timedelta(days=index), 10, 11, 9, 10, 100)
                    for index in range((end - start).days + 1)]

        remote.return_value.get_history.side_effect = history
        with TemporaryDirectory() as directory:
            metadata = download_history('CRYPTO', 'BTC/USDT', date(2022, 1, 1), date(2024, 12, 31), Path(directory))
            self.assertEqual(metadata['bar_count'], 1096)
            self.assertEqual(remote.return_value.get_history.call_count, 2)

    @patch('market_data.local_history.get_provider')
    def test_invalid_data_and_future_dates_are_not_saved(self, remote) -> None:
        remote.return_value.get_history.return_value = [
            HistoricalBar(date(2024, 1, 2), 10, 9, 11, 10, 100),
        ]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(MarketDataError):
                download_history('US', 'AAPL', date(2024, 1, 1), date(2024, 1, 3), root)
            self.assertFalse(list(root.rglob('*.json')))
            remote.reset_mock()
            with self.assertRaises(MarketDataError):
                download_history('US', 'AAPL', date(2024, 1, 1), date(2099, 1, 1), root)
            remote.assert_not_called()


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
    def test_minute_endpoint_returns_read_only_closed_bars(self, get_provider_mock) -> None:
        class MinuteProvider:
            def get_minute_bars(self, symbol, limit):
                self.symbol = symbol
                self.limit = limit
                return [MinuteBar(
                    timestamp=datetime(2025, 1, 2, 12, 1, tzinfo=timezone.utc),
                    open=10,
                    high=11,
                    low=9,
                    close=10.5,
                    volume=1000,
                )]

        provider = MinuteProvider()
        get_provider_mock.return_value = provider
        response = self.client.get(reverse('market_minute_data'), {
            'market': 'CRYPTO',
            'symbol': 'BTC/USDT',
            'limit': '10',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(provider.symbol, 'BTC/USDT')
        self.assertEqual(provider.limit, 10)
        self.assertEqual(response.json()['data']['interval'], '1m')
        self.assertEqual(response.json()['data']['bars'][0]['timestamp'], '2025-01-02T12:01:00+00:00')

    @patch('stockmarket.trading_views.LocalHistoryProvider')
    def test_portfolio_backtest_endpoint_runs_local_baseline(self, get_provider_mock) -> None:
        class PortfolioProvider:
            datasets = {}

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

    @patch('stockmarket.trading_views.LocalHistoryProvider')
    def test_leaky_forecast_endpoint_returns_gamma_metrics(self, get_provider_mock) -> None:
        class ForecastProvider:
            datasets = {}

            def get_history(self, symbol, start, end):
                prices = [100, 101, 102, 103, 104, 105, 105, 105, 105, 105, 105]
                return [HistoricalBar(
                    date=date(2025, 1, 1) + timedelta(days=index),
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    volume=1000,
                ) for index, price in enumerate(prices)]

        get_provider_mock.return_value = ForecastProvider()
        response = self.client.post(
            reverse('leaky_forecast_experiment'),
            data={
                'market': 'US',
                'symbol': 'AAPL',
                'train_window': 5,
                'horizon': 5,
                'gamma_values': [1.0, 0.5],
            },
            content_type='application/json',
        )

        payload = response.json()['data']
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload['experiment'], 'leaky_integrator_differenced_forecast')
        self.assertEqual(payload['symbol'], 'AAPL')
        self.assertEqual(payload['recommended_gamma'], 0.5)
        self.assertEqual(len(payload['metrics_by_gamma']), 2)


    @patch('stockmarket.trading_views.get_provider', side_effect=AssertionError('Network is forbidden'))
    @patch('market_data.local_history.get_provider', side_effect=AssertionError('Network is forbidden'))
    def test_research_endpoints_use_real_local_snapshot(self, _download, _remote) -> None:
        with TemporaryDirectory() as directory:
            with patch('market_data.local_history.get_provider') as source:
                source.return_value.get_history.return_value = [
                    HistoricalBar(date(2024, 1, 1) + timedelta(days=index), 100 + index, 101 + index, 99 + index, 100 + index, 1000)
                    for index in range(60)
                ]
                download_history('US', 'AAPL', date(2024, 1, 1), date(2024, 2, 29), Path(directory))
            with self.settings(HISTORICAL_DATA_DIR=directory):
                for endpoint in ('research_backtest', 'portfolio_backtest', 'leaky_forecast_experiment'):
                    with self.subTest(endpoint=endpoint):
                        response = self.client.post(reverse(endpoint), data={
                            'market': 'US', 'symbol': 'AAPL', 'symbols': ['AAPL'],
                            'start_date': '2024-01-01', 'end_date': '2024-02-29',
                        }, content_type='application/json')
                        self.assertEqual(response.status_code, 200, response.content)
                        payload = response.json()['data']
                        self.assertEqual(payload['data_source'], 'LocalHistoryProvider')
                        self.assertEqual(payload['datasets']['AAPL']['bar_count'], 60)
                        response = self.client.post(reverse(endpoint), data={
                            'market': 'US', 'symbol': 'MISSING', 'symbols': ['MISSING'],
                        }, content_type='application/json')
                        self.assertEqual(response.status_code, 400)
                        self.assertIn('network fallback is disabled', response.json()['error'])
        _download.assert_not_called()
        _remote.assert_not_called()


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
    def test_leaky_reconstruction_reduces_biased_recursive_error(self) -> None:
        standard = reconstruct_differenced_forecast(100, [1, 1, 1, 1], gamma=1.0)
        leaky = reconstruct_differenced_forecast(100, [1, 1, 1, 1], gamma=0.5)
        actual = [101, 101, 101, 101]

        standard_mae = sum(abs(forecast - value) for forecast, value in zip(standard, actual)) / len(actual)
        leaky_mae = sum(abs(forecast - value) for forecast, value in zip(leaky, actual)) / len(actual)

        self.assertEqual(standard, [101, 102, 103, 104])
        self.assertLess(leaky_mae, standard_mae)

    def test_leaky_experiment_scans_gamma_values(self) -> None:
        start = date(2025, 1, 1)
        prices = [100, 101, 102, 103, 104, 105, 105, 105, 105, 105, 105]
        bars = [HistoricalBar(start + timedelta(days=index), price, price, price, price, 1000)
                for index, price in enumerate(prices)]

        result = run_leaky_integrator_experiment(
            bars,
            train_window=5,
            horizon=5,
            gamma_values=[1.0, 0.5],
        )

        self.assertEqual(result['recommended_gamma'], 0.5)
        self.assertGreater(result['relative_mae_improvement'], 0)
        self.assertEqual(result['parameters']['sample_count'], len(prices) - 5 - 5)

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

    def test_entropy_risk_parity_reduces_weight_concentration(self) -> None:
        start = date(2025, 1, 1)
        bars_by_symbol = {
            'AAA': [HistoricalBar(start + timedelta(days=index), 100 + index, 100 + index,
                                  100 + index, 100 + index, 1000) for index in range(8)],
            'BBB': [HistoricalBar(start + timedelta(days=index), 100, 100, 100, 100, 1000)
                    for index in range(8)],
        }
        result = run_portfolio_baseline(
            bars_by_symbol,
            initial_cash=100000,
            strategy='entropy_risk_parity',
            lookback=2,
            entropy_strength=0.5,
        )

        weights = result['weight_history'][-1]['weights']
        self.assertAlmostEqual(sum(weights.values()), 1.0)
        self.assertLess(max(weights.values()), 1.0)
        self.assertEqual(result['parameters']['entropy_strength'], 0.5)

    def test_impact_cost_reduces_portfolio_equity(self) -> None:
        start = date(2025, 1, 1)
        bars_by_symbol = {
            symbol: [HistoricalBar(start + timedelta(days=index), price, price, price, price, 1000)
                     for index, price in enumerate(prices)]
            for symbol, prices in {
                'AAA': [100, 101, 99, 102, 98, 103, 97, 104],
                'BBB': [100, 99, 101, 98, 102, 97, 103, 96],
            }.items()
        }
        without_impact = run_portfolio_baseline(
            bars_by_symbol, 100000, strategy='tsmom', lookback=2,
        )
        with_impact = run_portfolio_baseline(
            bars_by_symbol, 100000, strategy='tsmom', lookback=2, impact_bps=50,
        )

        self.assertLess(with_impact['final_equity'], without_impact['final_equity'])