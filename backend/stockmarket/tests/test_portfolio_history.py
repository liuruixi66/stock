from contextlib import closing
from datetime import date
import hashlib
import json
from pathlib import Path
import sqlite3
from unittest import TestCase
from unittest.mock import patch

from market_data.portfolio_history import (
    PortfolioHistoryError, load_portfolio_history, portfolio_price_contract,
)
from stockmarket.tests import test_industry_universe


class PortfolioHistoryTests(TestCase):
    def setUp(self):
        self.fixture = test_industry_universe.IndustryUniverseTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.path = self.fixture.path
        self.universe = self.fixture.select()
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.executescript("""
                CREATE TABLE ts_daily (
                    ts_code TEXT, trade_date TEXT, open REAL, high REAL, low REAL,
                    close REAL, vol REAL, PRIMARY KEY(ts_code,trade_date)
                );
                CREATE TABLE ts_adj_factor (
                    ts_code TEXT, trade_date TEXT, adj_factor REAL,
                    PRIMARY KEY(ts_code,trade_date)
                );
            """)
            for exchange in ('SSE', 'SZSE'):
                conn.executemany('INSERT INTO ts_trade_cal VALUES (?,?,?)', [
                    (exchange, '20260108', 1), (exchange, '20260110', 0),
                ])
            for symbol in self.universe['selected_instruments']:
                for day in ('20260108', '20260109'):
                    conn.execute('INSERT INTO ts_daily VALUES (?,?,?,?,?,?,?)', (
                        symbol, day, 10, 12, 9, 11, 100,
                    ))
                    conn.execute('INSERT INTO ts_adj_factor VALUES (?,?,?)', (symbol, day, 2))

    def load(self):
        return load_portfolio_history(self.path, self.universe, date(2026, 1, 8), date(2026, 1, 10))

    def test_uses_same_day_tushare_factor_and_converts_volume_without_writing(self):
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        frame, sessions, _, provenance = self.load()
        self.assertEqual(len(frame), 12)
        self.assertEqual(len(sessions), 2)
        self.assertTrue((frame['open'] == 20).all())
        self.assertTrue((frame['close'] == 22).all())
        self.assertTrue((frame['volume'] == 10000).all())
        self.assertEqual(provenance['price_contract'], portfolio_price_contract())
        self.assertFalse(provenance['price_contract']['live_trading_eligible'])
        self.assertEqual(before, hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_missing_factor_is_not_filled_from_another_date(self):
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("DELETE FROM ts_adj_factor WHERE ts_code='600000.SH' AND trade_date='20260109'")
        with self.assertRaisesRegex(ValueError, 'adjustment factor'):
            self.load()

    def test_unexplained_quote_gap_blocks_training(self):
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("DELETE FROM ts_daily WHERE ts_code='600000.SH' AND trade_date='20260109'")
        with self.assertRaisesRegex(ValueError, 'Unexplained quote gaps'):
            self.load()

    def test_suspension_explains_gap_without_inserting_fake_quote(self):
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("DELETE FROM ts_daily WHERE ts_code='600000.SH' AND trade_date='20260109'")
            conn.execute("INSERT INTO ts_suspend_d VALUES ('600000.SH','20260109','S',NULL)")
        frame, _, suspensions, provenance = self.load()
        self.assertEqual(len(frame), 11)
        self.assertEqual(suspensions['600000.SH'], {'20260109'})
        self.assertEqual(provenance['stock_coverage']['600000.SH']['missing_quotes_explained_by_suspension'], 1)

    def test_calendar_gap_is_not_inferred_from_quotes(self):
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("DELETE FROM ts_trade_cal WHERE exchange='SSE' AND cal_date='20260110'")
        with self.assertRaisesRegex(ValueError, 'Incomplete or duplicate SSE calendar'):
            self.load()

    def test_nonpositive_factor_fails(self):
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute('UPDATE ts_adj_factor SET adj_factor=0')
        with self.assertRaisesRegex(ValueError, 'adjustment factor'):
            self.load()

    def test_reports_all_stock_gaps_instead_of_returning_partial_success(self):
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("DELETE FROM ts_daily WHERE ts_code IN ('600000.SH','600001.SH') AND trade_date='20260109'")
        with self.assertRaises(PortfolioHistoryError) as caught:
            self.load()
        self.assertEqual({issue['instrument'] for issue in caught.exception.issues},
                         {'600000.SH', '600001.SH'})

    def test_audit_cli_persists_blocked_status_and_returns_nonzero(self):
        from tools.audit_portfolio_history import main

        root = Path(self.fixture.temporary.name)
        source, output = root / 'universe.json', root / 'audit.json'
        source.write_text(json.dumps(self.universe), encoding='utf-8')
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute("DELETE FROM ts_daily WHERE ts_code='600000.SH' AND trade_date='20260109'")
        with patch('sys.argv', ['audit', str(source), '--start', '2026-01-08',
                               '--end', '2026-01-10', '--output', str(output)]):
            with self.assertRaises(SystemExit) as caught:
                main()
        self.assertEqual(caught.exception.code, 2)
        report = json.loads(output.read_text(encoding='utf-8'))
        self.assertEqual(report['status'], 'blocked')
        self.assertFalse(report['training_started'])
        self.assertEqual(report['issues'][0]['instrument'], '600000.SH')

    def test_audit_cli_never_overwrites_existing_evidence(self):
        from tools.audit_portfolio_history import main

        root = Path(self.fixture.temporary.name)
        source, output = root / 'universe.json', root / 'audit.json'
        source.write_text(json.dumps(self.universe), encoding='utf-8')
        output.write_text('existing evidence', encoding='utf-8')
        with patch('sys.argv', ['audit', str(source), '--output', str(output)]):
            with self.assertRaises(SystemExit) as caught:
                main()
        self.assertEqual(caught.exception.code, 1)
        self.assertEqual(output.read_text(encoding='utf-8'), 'existing evidence')
