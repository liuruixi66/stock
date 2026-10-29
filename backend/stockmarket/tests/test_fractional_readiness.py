from datetime import date
from contextlib import closing
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from unittest import TestCase

from tools.audit_fractional_execution_readiness import audit


class FractionalExecutionReadinessTests(TestCase):
    def fixture(self, root):
        source = root / 'search.json'
        source.write_text(json.dumps({
            'search_version': 2,
            'data_provenance': {'selected_instruments': ['600001.SH']},
        }), encoding='utf-8')
        database = root / 'stocks.db'
        with closing(sqlite3.connect(database)) as connection, connection:
            connection.executescript('''
                CREATE TABLE ts_trade_cal(exchange TEXT,cal_date TEXT,is_open INTEGER);
                CREATE TABLE ts_daily(ts_code TEXT,trade_date TEXT,open REAL,high REAL,
                    low REAL,close REAL,vol REAL,_source TEXT);
                CREATE TABLE ts_adj_factor(ts_code TEXT,trade_date TEXT,adj_factor REAL);
                CREATE TABLE ts_stk_limit(ts_code TEXT,trade_date TEXT,up_limit REAL,down_limit REAL);
                CREATE TABLE ts_suspend_d(ts_code TEXT,trade_date TEXT,suspend_type TEXT,suspend_timing TEXT);
                CREATE TABLE ts_dividend(ts_code TEXT,ann_date TEXT,imp_ann_date TEXT,
                    div_proc TEXT,record_date TEXT,ex_date TEXT,pay_date TEXT,div_listdate TEXT,
                    stk_div REAL,cash_div REAL,cash_div_tax REAL,_source TEXT);
                CREATE TABLE ts_namechange(ts_code TEXT);
                CREATE TABLE cn_tickers(symbol TEXT,code TEXT);
                CREATE TABLE cn_daily(symbol TEXT,date TEXT,open REAL,high REAL,low REAL,close REAL);
                INSERT INTO ts_trade_cal VALUES('SSE','20250102',1),('SSE','20250103',1);
                INSERT INTO ts_daily VALUES('600001.SH','20250102',10,11,9,10,100,'test');
                INSERT INTO ts_adj_factor VALUES('600001.SH','20250102',1);
                INSERT INTO ts_stk_limit VALUES('600001.SH','20250102',11,9);
                INSERT INTO cn_tickers VALUES('vendor','600001');
                INSERT INTO cn_daily VALUES('vendor','2025-01-02',5,5.5,4.5,5);
            ''')
        return source, database

    def test_audit_reports_coverage_disagreement_and_never_computes_returns(self):
        with TemporaryDirectory() as directory:
            source, database = self.fixture(Path(directory))
            before = database.read_bytes()
            result = audit(source, database, date(2025, 1, 2), date(2025, 1, 3), 200000)
            self.assertEqual(database.read_bytes(), before)
            self.assertEqual(result['initial_capital'], 200000)
            self.assertEqual(result['expected_open_sessions'], 2)
            self.assertEqual(result['calendar_gaps'], [])
            stock = result['stocks'][0]
            self.assertEqual(stock['missing_open_dates'], ['20250103'])
            self.assertEqual(stock['vendor_ohlc_mismatch_rows'], 1)
            self.assertEqual(stock['missing_limits_on_price_dates'], [])
            self.assertEqual(stock['missing_factors_on_price_dates'], [])
            self.assertEqual(result['status'], 'blocked')
            self.assertFalse(result['simulation_executed'])
            self.assertFalse(result['live_trading_eligible'])
            self.assertNotIn('backtests', result)

    def test_gaps_and_invalid_inputs_are_explicit(self):
        with TemporaryDirectory() as directory:
            source, database = self.fixture(Path(directory))
            with closing(sqlite3.connect(database)) as connection, connection:
                connection.execute('DELETE FROM ts_stk_limit')
                connection.execute('UPDATE ts_adj_factor SET adj_factor=0')
                connection.execute("UPDATE ts_trade_cal SET is_open=2 WHERE cal_date='20250103'")
                connection.execute('INSERT INTO ts_dividend VALUES(?,?,?,?,?,?,?,?,?,?,?,?)', (
                    '600001.SH', '20241201', None, '\u5b9e\u65bd', '20250101', '20250102',
                    None, None, 0, .1, .1, 'test',
                ))
            result = audit(source, database, date(2025, 1, 1), date(2025, 1, 3), 200000)
            self.assertEqual(result['calendar_gaps'], ['20250101'])
            self.assertEqual(result['invalid_calendar_dates'], ['20250103'])
            stock = result['stocks'][0]
            self.assertEqual(stock['missing_limits_on_price_dates'], ['20250102'])
            self.assertEqual(stock['invalid_factor_dates'], ['20250102'])
            self.assertEqual(len(stock['incomplete_implemented_actions']), 1)
            with self.assertRaises(ValueError):
                audit(source, database, date(2025, 1, 1), date(2025, 1, 3), float('nan'))

    def test_missing_tables_fail_closed_and_unsafe_symbols_are_rejected(self):
        with TemporaryDirectory() as directory:
            source, database = self.fixture(Path(directory))
            with closing(sqlite3.connect(database)) as connection, connection:
                connection.execute('DROP TABLE ts_stk_limit')
            result = audit(source, database, date(2025, 1, 2), date(2025, 1, 3), 200000)
            self.assertEqual(result['missing_tables'], ['ts_stk_limit'])
            self.assertFalse(result['simulation_executed'])
            source.write_text(json.dumps({
                'search_version': 2,
                'data_provenance': {'selected_instruments': ["600001.SH'; DROP TABLE ts_daily"]},
            }), encoding='utf-8')
            with self.assertRaises(ValueError):
                audit(source, database, date(2025, 1, 2), date(2025, 1, 3), 200000)
