import json
import os
import sys
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

from brokers import AccountSnapshot, BrokerAdapter, BrokerError, OrderResult, PositionSnapshot
from brokers.futu_broker import FutuBroker, from_futu_symbol, to_futu_symbol
from brokers.qmt_broker import from_qmt_symbol, to_qmt_symbol
from market_data import HistoricalBar, Market, MarketDataError, MinuteBar, Quote
from market_data.local_history import LocalHistoryProvider, download_history
from .analytics import build_account_analytics
from .models import SimulationAccount, SimulationOrder, SimulationPosition
from .paper_trading import TradingError, cancel_order, submit_order, sync_account
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


class FakeBroker(BrokerAdapter):
    """记录调用并返回预设结果的假券商，用于验证路由与本地账本隔离。"""

    code = 'FAKE'
    label = 'Fake'
    markets = frozenset({'A', 'US'})
    supports_live = True
    calls: list[tuple] = []
    place_result = OrderResult(status='SUBMITTED', broker_order_id='B-1', message='accepted')
    order_result = OrderResult(status='FILLED', broker_order_id='B-1', filled_quantity=Decimal('10'),
                               executed_price=Decimal('150.5'), message='done')
    snapshot = AccountSnapshot(cash=Decimal('5000'), market_value=Decimal('1505'), total_assets=Decimal('6505'), currency='USD')
    positions = [PositionSnapshot(symbol='AAPL', quantity=Decimal('10'), average_price=Decimal('150.5'))]

    def place_order(self, order):
        FakeBroker.calls.append(('place', order.symbol, order.side, order.quantity, self.account.trading_mode))
        return self.place_result

    def cancel_order(self, order):
        FakeBroker.calls.append(('cancel', order.broker_order_id))
        return OrderResult(status='CANCELLED', broker_order_id=order.broker_order_id, message='cancelled')

    def get_order(self, order):
        FakeBroker.calls.append(('get_order', order.broker_order_id))
        return self.order_result

    def get_account(self):
        return self.snapshot

    def get_positions(self):
        return list(self.positions)


class ExternalBrokerRoutingTests(TestCase):
    def setUp(self) -> None:
        FakeBroker.calls = []
        self.account = SimulationAccount.objects.create(
            name='富途美股模拟', market='US', currency='USD', broker='FUTU', broker_account_id='123',
            initial_cash=Decimal('6505'), cash=Decimal('6505'),
        )
        patcher = patch('stockmarket.paper_trading.get_broker', side_effect=lambda account: FakeBroker(account))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_external_order_is_forwarded_and_ledger_untouched(self) -> None:
        order = submit_order(self.account.id, 'aapl', 'BUY', Decimal('10'))

        self.account.refresh_from_db()
        self.assertEqual(order.status, 'SUBMITTED')
        self.assertEqual(order.broker_order_id, 'B-1')
        self.assertEqual(self.account.cash, Decimal('6505'))
        self.assertFalse(SimulationPosition.objects.filter(account=self.account).exists())
        self.assertEqual(FakeBroker.calls, [('place', 'AAPL', 'BUY', Decimal('10'), 'PAPER')])

    def test_external_us_order_rejects_fractional_shares(self) -> None:
        with self.assertRaises(TradingError):
            submit_order(self.account.id, 'AAPL', 'BUY', Decimal('0.5'))
        self.assertEqual(FakeBroker.calls, [])

    def test_broker_error_becomes_rejected_order(self) -> None:
        with patch.object(FakeBroker, 'place_order', side_effect=BrokerError('OpenD 未启动')):
            order = submit_order(self.account.id, 'AAPL', 'BUY', Decimal('10'))
        self.assertEqual(order.status, 'REJECTED')
        self.assertIn('OpenD', order.message)

    def test_live_mode_requires_global_switch(self) -> None:
        self.account.trading_mode = 'LIVE'
        self.account.save()
        with patch.dict(os.environ, {'LIVE_TRADING_ENABLED': ''}):
            with self.assertRaisesRegex(TradingError, 'LIVE_TRADING_ENABLED'):
                submit_order(self.account.id, 'AAPL', 'BUY', Decimal('10'))
        with patch.dict(os.environ, {'LIVE_TRADING_ENABLED': '1'}):
            order = submit_order(self.account.id, 'AAPL', 'BUY', Decimal('10'))
        self.assertEqual(order.status, 'SUBMITTED')
        self.assertEqual(FakeBroker.calls[-1][-1], 'LIVE')

    def test_sync_replaces_positions_and_finalizes_open_orders(self) -> None:
        order = submit_order(self.account.id, 'AAPL', 'BUY', Decimal('10'))
        SimulationPosition.objects.create(account=self.account, symbol='STALE', quantity=1, average_price=1)

        sync_account(self.account)

        order.refresh_from_db()
        self.account.refresh_from_db()
        self.assertEqual(order.status, 'FILLED')
        self.assertEqual(order.filled_quantity, Decimal('10'))
        self.assertEqual(order.executed_price, Decimal('150.5'))
        self.assertEqual(self.account.cash, Decimal('5000'))
        self.assertIsNotNone(self.account.last_synced_at)
        self.assertEqual(
            list(SimulationPosition.objects.filter(account=self.account).values_list('symbol', 'quantity')),
            [('AAPL', Decimal('10'))],
        )

    def test_cancel_open_external_order(self) -> None:
        order = submit_order(self.account.id, 'AAPL', 'BUY', Decimal('10'), 'LIMIT', Decimal('100'))
        cancelled = cancel_order(order.id)
        self.assertEqual(cancelled.status, 'CANCELLED')
        self.assertIn(('cancel', 'B-1'), FakeBroker.calls)
        with self.assertRaises(TradingError):
            cancel_order(order.id)

    def test_simulated_pending_limit_order_can_be_cancelled_locally(self) -> None:
        sim = SimulationAccount.objects.create(
            name='内置模拟', market='US', currency='USD', initial_cash=Decimal('1000'), cash=Decimal('1000'),
        )
        with patch('stockmarket.paper_trading.get_provider', return_value=FakeProvider()):
            order = submit_order(sim.id, 'AAPL', 'BUY', Decimal('1'), 'LIMIT', Decimal('1'))
        self.assertEqual(order.status, 'PENDING')
        self.assertEqual(cancel_order(order.id).status, 'CANCELLED')
        self.assertEqual(FakeBroker.calls, [])


class BrokerAccountApiTests(TestCase):
    def test_create_external_account_uses_broker_equity_as_baseline(self) -> None:
        with patch('stockmarket.paper_trading.adapter_class', return_value=FakeBroker), \
                patch('stockmarket.paper_trading.get_broker', side_effect=lambda account: FakeBroker(account)):
            response = self.client.post(reverse('paper_accounts'), data=json.dumps({
                'name': 'IB 模拟', 'market': 'US', 'broker': 'IB', 'broker_account_id': 'DU123', 'trading_mode': 'PAPER',
            }), content_type='application/json')

        self.assertEqual(response.status_code, 201, response.content)
        payload = response.json()['data']
        self.assertEqual(payload['broker'], 'IB')
        self.assertTrue(payload['is_external'])
        self.assertEqual(payload['initial_cash'], 6505.0)
        self.assertEqual(payload['cash'], 5000.0)
        self.assertEqual(SimulationPosition.objects.filter(account_id=payload['id']).count(), 1)

    def test_create_external_account_fails_fast_when_broker_unreachable(self) -> None:
        with patch('stockmarket.paper_trading.adapter_class', return_value=FakeBroker), \
                patch.object(FakeBroker, 'get_account', side_effect=BrokerError('TWS 未启动')):
            response = self.client.post(reverse('paper_accounts'), data=json.dumps({
                'name': 'IB 模拟', 'market': 'US', 'broker': 'IB',
            }), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('TWS', response.json()['error'])
        self.assertFalse(SimulationAccount.objects.exists())

    def test_market_not_supported_by_broker_is_rejected(self) -> None:
        response = self.client.post(reverse('paper_accounts'), data=json.dumps({
            'name': 'QMT 美股', 'market': 'US', 'broker': 'QMT',
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('不支持', response.json()['error'])

    def test_simulated_account_defaults_are_unchanged(self) -> None:
        response = self.client.post(reverse('paper_accounts'), data=json.dumps({
            'name': 'A股研究账户', 'market': 'A', 'initial_cash': 100000,
        }), content_type='application/json')
        payload = response.json()['data']
        self.assertEqual(payload['broker'], 'SIM')
        self.assertFalse(payload['is_external'])
        self.assertEqual(payload['trading_mode'], 'PAPER')

    def test_brokers_endpoint_lists_catalog_without_importing_sdks(self) -> None:
        response = self.client.get(reverse('paper_brokers'))
        data = response.json()['data']
        codes = [item['code'] for item in data['brokers']]
        self.assertEqual(codes, ['SIM', 'FUTU', 'QMT', 'IB'])
        futu = next(item for item in data['brokers'] if item['code'] == 'FUTU')
        self.assertEqual(futu['markets'], ['A', 'US'])
        self.assertIn('FUTU_OPEND_PORT', futu['env_vars'])
        self.assertIsInstance(data['live_trading_enabled'], bool)

    def test_summary_reports_sync_error_but_still_returns_cached_data(self) -> None:
        account = SimulationAccount.objects.create(
            name='富途', market='US', currency='USD', broker='FUTU', initial_cash=Decimal('100'), cash=Decimal('100'),
        )
        with patch('stockmarket.trading_views.sync_account', side_effect=BrokerError('OpenD 未连接')):
            response = self.client.get(reverse('paper_account_summary', args=[account.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('OpenD', response.json()['data']['sync_error'])
        self.assertEqual(response.json()['data']['cash'], 100.0)


class BrokerSymbolMappingTests(SimpleTestCase):
    def test_futu_symbols(self) -> None:
        self.assertEqual(to_futu_symbol('A', '600519'), 'SH.600519')
        self.assertEqual(to_futu_symbol('A', '000001'), 'SZ.000001')
        self.assertEqual(to_futu_symbol('A', '430047'), 'BJ.430047')
        self.assertEqual(to_futu_symbol('US', 'aapl'), 'US.AAPL')
        self.assertEqual(to_futu_symbol('US', 'HK.00700'), 'HK.00700')
        self.assertEqual(from_futu_symbol('US.AAPL'), 'AAPL')

    def test_qmt_symbols(self) -> None:
        self.assertEqual(to_qmt_symbol('600519'), '600519.SH')
        self.assertEqual(to_qmt_symbol('510300'), '510300.SH')
        self.assertEqual(to_qmt_symbol('159915'), '159915.SZ')
        self.assertEqual(to_qmt_symbol('920001'), '920001.BJ')
        self.assertEqual(from_qmt_symbol('000001.SZ'), '000001')

    def test_missing_sdk_raises_actionable_error(self) -> None:
        account = SimulationAccount(name='x', market='US', currency='USD', broker='FUTU', trading_mode='PAPER')
        with patch.dict(sys.modules, {'futu': None}):
            with self.assertRaisesRegex(BrokerError, 'pip install futu-api'):
                FutuBroker(account).get_account()


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