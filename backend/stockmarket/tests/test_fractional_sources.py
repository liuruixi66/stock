from datetime import date, timedelta
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from tools.verify_fractional_sources import (
    compare, parse_actions, parse_prices, verify, windows,
)
from tools.collect_fractional_announcement import parse_distribution


class ExternalPriceVerificationTests(TestCase):
    def setUp(self):
        self.start = date(2025, 1, 2)
        self.end = date(2025, 1, 3)
        self.local = {
            self.start: {
                'open': 10, 'high': 11, 'low': 9, 'close': 10,
                'adj_close': 9, 'dividends': 0, 'splits': 0,
            },
            self.end: {
                'open': 10, 'high': 11, 'low': 9, 'close': 10,
                'adj_close': 9, 'dividends': 0, 'splits': 0,
            },
        }
        self.external = {day: {key: row[key] for key in ('open', 'high', 'low', 'close')}
                         for day, row in self.local.items()}

    def test_windows_are_contiguous_bounded_and_cover_leap_years(self):
        start, end = date(2006, 10, 16), date(2026, 10, 14)
        intervals = list(windows(start, end))
        self.assertEqual(intervals[0][0], start)
        self.assertEqual(intervals[-1][1], end)
        for index, (begin, stop) in enumerate(intervals):
            self.assertLessEqual((stop - begin).days, 729)
            if index:
                self.assertEqual(intervals[index - 1][1] + timedelta(days=1), begin)

    def test_unadjusted_tencent_field_order_is_correct(self):
        payload = {'code': 0, 'data': {'sh600001': {
            'day': [['2025-01-02', '10', '10.5', '11', '9', '100']],
        }}}
        prices = parse_prices(payload, 'sh600001', self.start, self.end)
        self.assertEqual(prices[self.start], {'open': 10, 'close': 10.5, 'high': 11, 'low': 9})
        payload['data']['sh600001'] = {'qfqday': [['2025-01-02', '10', '10', '11', '9', '100']]}
        with self.assertRaisesRegex(ValueError, 'unadjusted'):
            parse_prices(payload, 'sh600001', self.start, self.end)

    def test_bad_duplicates_out_of_range_or_nonfinite_prices_fail(self):
        row = ['2025-01-02', '10', '10', '11', '9', '100']
        for rows in ([row, row], [['2024-01-01', *row[1:]]],
                     [['2025-01-02', 'nan', *row[2:]]]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                parse_prices({'code': 0, 'data': {'sh600001': {'day': rows}}},
                             'sh600001', self.start, self.end)
        with self.assertRaisesRegex(ValueError, 'object'):
            parse_prices({'code': 0, 'data': None}, 'sh600001', self.start, self.end)

    def test_missing_reference_days_are_not_counted_as_success(self):
        self.external.pop(self.end)
        result = compare(self.local, self.external, [])
        self.assertEqual(result['missing_reference_dates'], ['2025-01-03'])
        self.assertFalse(result['ohlc_crosscheck_passed'])

    def test_price_tolerance_handles_float_storage_but_rejects_one_cent(self):
        self.external[self.end]['close'] = 10.0000004
        self.assertTrue(compare(self.local, self.external, [])['ohlc_crosscheck_passed'])
        self.external[self.end]['close'] = 10.01
        result = compare(self.local, self.external, [])
        self.assertFalse(result['ohlc_crosscheck_passed'])
        self.assertEqual(result['price_mismatch_count'], 1)
        self.assertFalse(result['live_trading_eligible'])

    def test_factor_jump_without_action_is_reported_not_repaired(self):
        self.local[self.end]['adj_close'] = 10
        result = compare(self.local, self.external, [])
        self.assertEqual(len(result['unexplained_factor_changes']), 1)
        self.assertEqual(self.local[self.end]['adj_close'], 10)
        actions = [{'date': str(self.end), 'cash_per_share': 0.5, 'bonus_share_ratio': None}]
        result = compare(self.local, self.external, actions)
        self.assertEqual(result['unexplained_factor_changes'], [])
        self.assertFalse(result['corporate_action_checks'][0]['cash_matches'])

    def test_actions_are_per_ten_shares_and_nulls_stay_unknown(self):
        record = {
            'SECURITY_CODE': '600001', 'ASSIGN_PROGRESS': '实施分配',
            'EX_DIVIDEND_DATE': '2025-01-03 00:00:00', 'PRETAX_BONUS_RMB': 5,
            'BONUS_IT_RATIO': 3,
        }
        payload = {'success': True, 'result': {'pages': 1, 'data': [record]}}
        actions, pages = parse_actions(payload, '600001')
        self.assertEqual(pages, 1)
        self.assertEqual(actions[0]['cash_per_share'], 0.5)
        self.assertEqual(actions[0]['bonus_share_ratio'], 0.3)
        record['PRETAX_BONUS_RMB'] = None
        record['BONUS_IT_RATIO'] = None
        actions, _ = parse_actions(payload, '600001')
        self.assertIsNone(actions[0]['cash_per_share'])
        self.assertIsNone(actions[0]['bonus_share_ratio'])
        self.assertFalse(actions[0]['payment_date_verified'])
        record['ASSIGN_PROGRESS'] = '董事会预案'
        with self.assertRaisesRegex(ValueError, 'proposal'):
            parse_actions(payload, '600001')

    def test_invalid_action_payloads_fail_instead_of_asserting_no_actions(self):
        for payload in ({'success': False}, {'success': True, 'result': None},
                        {'success': True, 'result': {'pages': 0, 'data': []}}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                parse_actions(payload, '600001')
        with self.assertRaisesRegex(ValueError, 'object'):
            parse_actions({'success': True, 'result': {'pages': 1, 'data': [None]}}, '600001')

    def test_stored_events_without_external_reference_are_disclosed(self):
        self.local[self.end]['splits'] = 1.3
        result = compare(self.local, self.external, [])
        self.assertEqual(result['stored_actions_without_reference'][0]['field'], 'splits')

    def test_network_errors_persist_as_failed_verification_not_success(self):
        import sqlite3
        from contextlib import closing
        import requests

        with TemporaryDirectory() as directory:
            root = Path(directory)
            source, database, output = root / 'result.json', root / 'db.sqlite', root / 'verification'
            source.write_text(json.dumps({
                'parameters': {'train_start': '2025-01-02', 'test_end': '2025-01-03'},
                'data_provenance': {'selected_instruments': ['600001.SH']},
            }), encoding='utf-8')
            with closing(sqlite3.connect(database)) as connection, connection:
                connection.executescript('''
                    CREATE TABLE cn_tickers (symbol TEXT, code TEXT);
                    CREATE TABLE cn_daily (
                        symbol TEXT, date TEXT, open REAL, high REAL, low REAL, close REAL,
                        adj_close REAL, dividends REAL, splits REAL
                    );
                    INSERT INTO cn_tickers VALUES ('600001.SS','600001');
                    INSERT INTO cn_daily VALUES ('600001.SS','2025-01-02',10,11,9,10,9,0,0);
                ''')
            with patch('tools.verify_fractional_sources.fetch', side_effect=requests.Timeout('offline')), \
                    patch('tools.verify_fractional_sources.time.sleep'):
                result = verify(source, database, output)
            self.assertFalse(result['all_ohlc_crosschecks_passed'])
            self.assertFalse(result['all_reference_fetches_complete'])
            self.assertFalse(result['training_started'])
            self.assertEqual(len(result['stocks'][0]['errors']), 2)
            self.assertTrue((output / 'summary.json').is_file())
            html = (output / 'index.html').read_text(encoding='utf-8')
            self.assertIn('核验未通过', html)
            self.assertIn('不启动重训', html)
            self.assertTrue((output / 'evidence' / '600001-stored-snapshot.json').is_file())
            with self.assertRaisesRegex(ValueError, 'overwrite'):
                verify(source, database, output)
            data = json.loads(source.read_text(encoding='utf-8'))
            data['parameters']['train_start'] = '2020-01-01'
            source.write_text(json.dumps(data), encoding='utf-8')
            response = requests.Response()
            response.status_code = 501
            unavailable = requests.HTTPError('server unavailable', response=response)
            with patch('tools.verify_fractional_sources.fetch', side_effect=unavailable) as fetcher, \
                    patch('tools.verify_fractional_sources.time.sleep'):
                result = verify(source, database, root / 'unavailable')
            self.assertEqual(fetcher.call_count, 2)  # One actual request per source.
            self.assertFalse(result['research_crosscheck_passed'])
            self.assertTrue(any('remaining requests are not sent' in item['error']
                                for item in result['stocks'][0]['errors']))


class AnnouncementDistributionTests(TestCase):
    def announcement(self):
        return (
            '证券代码：600055 A 股每股现金红利0.15元 每股转增股份0.40股 '
            '股份类别 股权登记日 最后交易日 除权（息）日 新增无限售条件流通股份上市日 '
            '现金红利发放日 Ａ股 2017/6/1 － 2017/6/2 2017/6/5 2017/6/2 '
            '差异化分红送转：否'
        )

    def test_reads_explicit_dates_and_per_share_amounts(self):
        event = parse_distribution(self.announcement(), '600055')
        self.assertEqual(event['cash_per_share_pretax'], 0.15)
        self.assertEqual(event['transfer_shares_per_share'], 0.4)
        self.assertEqual(event['record_date'], '2017-06-01')
        self.assertEqual(event['ex_date'], '2017-06-02')
        self.assertEqual(event['new_share_listing_date'], '2017-06-05')
        self.assertEqual(event['cash_payment_date'], '2017-06-02')
        self.assertFalse(event['live_trading_eligible'])

    def test_ambiguous_or_missing_tables_require_manual_review(self):
        for text in (
            self.announcement().replace('差异化分红送转：否', '差异化分红送转：是'),
            self.announcement().replace('2017/6/5', ''),
            self.announcement().replace('2017/6/1', '2017/6/6'),
            self.announcement().replace('0.15元', '未确定'),
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_distribution(text, '600055')

    def test_symbol_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'security code'):
            parse_distribution(self.announcement(), '600058')
