from contextlib import closing
from datetime import date
import hashlib
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from market_data.industry_universe import (
    exclude_universe_instruments, select_industry_leaders, verify_industry_universe,
)


class IndustryUniverseTests(TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / 'stocks.db'
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.executescript("""
                CREATE TABLE ts_stock_basic (
                    ts_code TEXT PRIMARY KEY, name TEXT, market TEXT, exchange TEXT,
                    curr_type TEXT, list_status TEXT, list_date TEXT, delist_date TEXT,
                    _fetched_at TEXT
                );
                CREATE TABLE cn_info (
                    symbol TEXT PRIMARY KEY, name TEXT, industry TEXT, updated_at TEXT
                );
                CREATE TABLE ts_daily_basic (
                    ts_code TEXT, trade_date TEXT, total_mv REAL,
                    PRIMARY KEY (ts_code, trade_date)
                );
                CREATE TABLE ts_suspend_d (
                    ts_code TEXT, trade_date TEXT, suspend_type TEXT, suspend_timing TEXT
                );
                CREATE TABLE ts_trade_cal (
                    exchange TEXT, cal_date TEXT, is_open REAL
                );
                CREATE TABLE ts_download_progress (
                    api TEXT, params TEXT, status TEXT, row_count INTEGER
                );
            """)
            for api in ('daily_basic', 'suspend_d'):
                conn.execute('INSERT INTO ts_download_progress VALUES (?,?,?,?)', (
                    api, json.dumps({'start_date': '20260101', 'end_date': '20260109'}),
                    'done', 10,
                ))
            conn.executemany('INSERT INTO ts_trade_cal VALUES (?,?,?)', [
                (exchange, '20260109', 1) for exchange in ('SSE', 'SZSE')
            ])
        for index in range(7):
            self.add_stock(f'60000{index}.SH', cap=100 - index, industry='Banks')
        self.add_stock('000001.SZ', cap=50, industry='Insurance')

    def add_stock(self, symbol, *, cap=10, industry='Banks', name='Stock',
                  market='\u4e3b\u677f', currency='CNY', status='L', day='20260109'):
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute('INSERT INTO ts_stock_basic VALUES (?,?,?,?,?,?,?,?,?)', (
                symbol, name, market, 'SSE' if symbol.endswith('.SH') else 'SZSE',
                currency, status, '20000101', None, '2026-01-09 20:00:00',
            ))
            conn.execute('INSERT INTO cn_info VALUES (?,?,?,?)', (
                symbol.replace('.SH', '.SS'), name, industry, '2026-01-09 20:00:00',
            ))
            if cap is not None:
                conn.execute('INSERT INTO ts_daily_basic VALUES (?,?,?)', (symbol, day, cap))

    def select(self, **options):
        return select_industry_leaders(self.path, as_of=date(2026, 1, 10), **options)

    def test_selects_five_per_industry_and_keeps_small_industries(self):
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        result = self.select()
        self.assertEqual(result['market_cap_date'], '2026-01-09')
        self.assertEqual(result['industry_count'], 2)
        self.assertEqual(result['stock_count'], 6)
        self.assertEqual(result['selected_instruments'], [
            '000001.SZ', '600000.SH', '600001.SH', '600002.SH', '600003.SH', '600004.SH',
        ])
        self.assertEqual(result['undersized_industries'], {'Insurance': 1})
        self.assertEqual(result['excluded_counts']['below_industry_top_n'], 2)
        self.assertEqual(result['ranking_field'], 'total_mv')
        self.assertEqual(result['market_cap_unit'], 'CNY_10000')
        self.assertFalse(result['historical_st_verified'])
        self.assertFalse(result['live_trading_eligible'])
        self.assertTrue(result['lookahead_bias'])
        self.assertEqual(before, hashlib.sha256(self.path.read_bytes()).hexdigest())
        verify_industry_universe(result)

    def test_excludes_st_star_st_and_suspended_before_ranking(self):
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("UPDATE ts_stock_basic SET name='*ST Example' WHERE ts_code='600000.SH'")
            conn.execute("UPDATE cn_info SET name='ST Example' WHERE symbol='600001.SS'")
            conn.execute("INSERT INTO ts_suspend_d VALUES ('600002.SH','20260109','S',NULL)")
        result = self.select()
        self.assertEqual(result['excluded_counts']['current_st_name'], 2)
        self.assertEqual(result['excluded_counts']['suspended_on_selection_date'], 1)
        self.assertEqual(result['undersized_industries']['Banks'], 4)
        self.assertNotIn('600000.SH', result['selected_instruments'])

    def test_excludes_other_boards_currencies_and_unlisted(self):
        self.add_stock('688001.SH', market='\u79d1\u521b\u677f')
        self.add_stock('300001.SZ', market='\u521b\u4e1a\u677f')
        self.add_stock('900001.SH', currency='USD')
        self.add_stock('600008.SH', status='D')
        result = self.select()
        self.assertEqual(result['stock_count'], 6)
        for symbol in ('688001.SH', '300001.SZ', '900001.SH', '600008.SH'):
            self.assertNotIn(symbol, result['selected_instruments'])

    def test_missing_industry_or_same_day_cap_is_not_filled(self):
        self.add_stock('600009.SH', industry=None, cap=999)
        self.add_stock('600010.SH', cap=999, day='20260108')
        self.add_stock('600011.SH', cap=-1)
        result = self.select()
        self.assertEqual(result['excluded_counts']['missing_industry'], 1)
        self.assertEqual(result['excluded_counts']['missing_same_day_market_cap'], 1)
        self.assertEqual(result['excluded_counts']['invalid_market_cap'], 1)

    def test_ties_are_broken_by_symbol(self):
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute('UPDATE ts_daily_basic SET total_mv=100')
        self.assertEqual(self.select()['industries']['Banks'][-1]['instrument'], '600004.SH')

    def test_explicit_exclusions_are_signed_and_not_backfilled(self):
        source = self.select()
        result = exclude_universe_instruments(
            source, {'600000.SH': 'user_excluded_historical_data_gaps'},
        )
        self.assertEqual(result['stock_count'], 5)
        self.assertNotIn('600000.SH', result['selected_instruments'])
        self.assertEqual(
            [row['instrument'] for row in result['industries']['Banks']],
            ['600001.SH', '600002.SH', '600003.SH', '600004.SH'],
        )
        self.assertEqual(
            result['excluded_counts']['user_excluded_historical_data_gaps'], 1,
        )
        self.assertEqual(result['parent_signature'], source['signature'])
        self.assertEqual(result['exclusion_policy'],
                         'explicit_user_exclusions_without_industry_backfill')
        verify_industry_universe(result)
        with self.assertRaisesRegex(ValueError, 'outside the universe'):
            exclude_universe_instruments(source, {'999999.SH': 'not selected'})

    def test_nonfinite_cap_is_excluded_with_serializable_audit(self):
        self.add_stock('600009.SH', cap=float('inf'))
        self.add_stock('600010.SH', cap='invalid')
        result = self.select()
        self.assertEqual(result['excluded_counts']['invalid_market_cap'], 2)
        json.dumps(result, allow_nan=False)

    def test_missing_calendar_is_an_error(self):
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("DELETE FROM ts_trade_cal WHERE exchange='SZSE'")
        with self.assertRaisesRegex(ValueError, 'SZSE calendar'):
            self.select()

    def test_one_stock_download_does_not_prove_market_wide_coverage(self):
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("DELETE FROM ts_download_progress WHERE api='daily_basic'")
            conn.execute('INSERT INTO ts_download_progress VALUES (?,?,?,?)', (
                'daily_basic', json.dumps({'ts_code': '600000.SH',
                                           'start_date': '20260101', 'end_date': '20260109'}),
                'done', 10,
            ))
        with self.assertRaisesRegex(ValueError, 'market-wide daily_basic'):
            self.select()

    def test_missing_same_day_metric_does_not_trigger_cross_date_fallback(self):
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("UPDATE ts_daily_basic SET trade_date='20260108' WHERE ts_code='600000.SH'")
        result = self.select()
        self.assertNotIn('600000.SH', result['selected_instruments'])
        self.assertIn('600005.SH', result['selected_instruments'])

    def test_empty_universe_and_invalid_size_raise(self):
        for value in (0, -1, True, 1.5):
            with self.subTest(per_industry=value), self.assertRaisesRegex(ValueError, 'positive integer'):
                self.select(per_industry=value)
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("UPDATE ts_stock_basic SET list_status='D'")
        with self.assertRaisesRegex(ValueError, 'empty universe'):
            self.select()

    def test_s_star_st_is_excluded_and_regular_english_stock_name_is_not(self):
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("UPDATE ts_stock_basic SET name='S*ST Example' WHERE ts_code='600000.SH'")
        result = self.select()
        self.assertNotIn('600000.SH', result['selected_instruments'])
        self.assertIn('600001.SH', result['selected_instruments'])

    def test_partial_newer_market_cap_day_is_rejected_not_silently_used(self):
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("INSERT INTO ts_daily_basic VALUES ('600000.SH','20260110',999)")
        with self.assertRaisesRegex(ValueError, 'completed market-wide daily_basic'):
            select_industry_leaders(self.path, as_of=date(2026, 1, 11))

    def test_requires_suspension_coverage_and_calendar(self):
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("DELETE FROM ts_download_progress WHERE api='suspend_d'")
        with self.assertRaisesRegex(ValueError, 'completed market-wide suspend_d'):
            self.select()

    def test_rejects_unknown_suspension_type(self):
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("INSERT INTO ts_suspend_d VALUES ('600002.SH','20260109','UNKNOWN',NULL)")
        with self.assertRaisesRegex(ValueError, 'suspension type'):
            self.select()

    def test_explicit_date_never_uses_a_different_day(self):
        with self.assertRaisesRegex(ValueError, 'market-cap rows'):
            self.select(market_cap_date=date(2026, 1, 8))
        with self.assertRaisesRegex(ValueError, 'completed past date'):
            self.select(market_cap_date=date(2026, 1, 10))

    def test_rejects_tampering_and_not_a_training_result(self):
        result = self.select()
        result['industries']['Banks'][0]['total_market_cap'] += 1
        with self.assertRaisesRegex(ValueError, 'signature'):
            verify_industry_universe(result)

    def test_cli_uses_separate_run_kind_and_writes_readable_csv(self):
        from functools import partial
        from research.experiment_runs import latest_completed, tracked_run
        from tools.select_industry_leaders import main

        root = Path(self.temporary.name) / 'runs'
        with patch('sys.argv', ['select', '--database', str(self.path)]), patch(
            'tools.select_industry_leaders.select_industry_leaders', side_effect=lambda *a, **k: self.select(),
        ), patch('tools.select_industry_leaders.tracked_run', partial(tracked_run, root=root)):
            main()
        run = latest_completed(root)
        self.assertEqual(run['kind'], 'portfolio-universe')
        self.assertIsNone(latest_completed(root, 'fractional-training'))
        report = json.loads(Path(run['artifact']).read_text(encoding='utf-8'))
        verify_industry_universe(report)
        self.assertTrue((root / run['run_id'] / 'industry-leaders.csv').is_file())
