from datetime import date, timedelta
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory

import pandas as pd
from django.test import SimpleTestCase

from research.fractional_forecast import DifferencingError, validate_prices
from tools.replay_fractional_execution import replay
from tools.audit_fractional_prices import audit
from market_data.price_basis import research_price_contract
from research.database_fractional import load_fractional_database
from research.fractional_forecast import ForecastConfig


class FractionalReplayTests(SimpleTestCase):
    def add_versioned_policy(self, source, database):
        data = json.loads(source.read_text(encoding='utf-8'))
        current = audit(source, database)['当前指纹']
        data['price_contract'] = research_price_contract()
        data['data_provenance']['price_contract'] = research_price_contract()
        data['data_provenance']['vendor_ohlc_sha256'] = current['供应商OHLC行情SHA256']
        data['data_provenance']['corporate_actions_sha256'] = current['公司行动SHA256']
        source.write_text(json.dumps(data), encoding='utf-8')

    def create_inputs(self, root):
        database = root / 'stocks.db'
        start = date(2025, 1, 1)
        records, forecasts = [], []
        with closing(sqlite3.connect(database)) as connection, connection:
            connection.executescript('''
                CREATE TABLE cn_tickers (symbol TEXT, code TEXT);
                CREATE TABLE cn_daily (
                    symbol TEXT, date TEXT, open REAL, high REAL, low REAL,
                    close REAL, adj_close REAL, volume REAL, dividends REAL, splits REAL
                );
            ''')
            for code, price in [('600001', 10.0), ('600002', 10.001)]:
                connection.execute('INSERT INTO cn_tickers VALUES (?,?)', (code + '.SS', code))
                for offset in range(4):
                    day = start + timedelta(days=offset)
                    connection.execute('INSERT INTO cn_daily VALUES (?,?,?,?,?,?,?,?,?,?)', (
                        code + '.SS', day.isoformat(), price, price, price, price,
                        price * 2, 1000, 0, 0,
                    ))
                    records.append({
                        'date': day, 'instrument': code + '.SH',
                        'open': price * 2, 'high': price * 2, 'low': price * 2,
                        'close': price * 2, 'volume': 1000.0,
                    })
                    if offset < 3:
                        forecasts.append({
                            'date': day.isoformat(), 'instrument': code + '.SH',
                            'predicted_return': 0.1,
                        })
        frame = validate_prices(pd.DataFrame(records))
        digest = hashlib.sha256(
            frame.to_csv(index=False, float_format='%.12g', lineterminator='\n').encode('utf-8'),
        ).hexdigest()
        source = root / 'experiment.json'
        result = {
            'parameters': {
                'train_start': '2024-01-01', 'test_start': '2025-01-01',
                'test_end': '2025-01-04', 'initial_capital': 1005,
                'buy_cost': 0.0005, 'sell_cost': 0.001,
                'signal_threshold': 0.002, 'seed': 43,
            },
            'data_provenance': {
                'selected_instruments': ['600001.SH', '600002.SH'],
                'selected_prices_sha256': digest,
                'universe_selection_date': '2025-01-01', 'eligible_universe_size': 2,
            },
            'forecasts': {'de_prado': forecasts, 'log_return': forecasts},
        }
        source.write_text(json.dumps(result), encoding='utf-8')
        return source, database

    def test_replays_identical_subsample_and_saved_forecasts(self):
        with TemporaryDirectory() as directory:
            source, database = self.create_inputs(Path(directory))
            result = replay(source, database)
        self.assertEqual(result['股票池筛选']['入选股票'], ['600001.SH'])
        self.assertEqual(result['股票池筛选']['通过检查股票数量'], 1)
        self.assertTrue(result['股票池筛选']['原始行情SHA256核验通过'])
        self.assertEqual(result['子样本原模拟']['分数差分LSTM']['缺失预测数量'], 0)
        self.assertEqual(result['有限交易约束模拟']['分数差分LSTM']['缺失预测数量'], 0)
        self.assertEqual(result['有限交易约束模拟']['分数差分LSTM']['成交笔数'], 0)

    def test_price_changes_after_training_are_rejected(self):
        with TemporaryDirectory() as directory:
            source, database = self.create_inputs(Path(directory))
            with closing(sqlite3.connect(database)) as connection, connection:
                connection.execute('UPDATE cn_daily SET adj_close=adj_close*1.01')
            with self.assertRaisesRegex(DifferencingError, 'price digest'):
                replay(source, database)

    def test_versioned_replay_checks_both_nominal_and_action_fingerprints(self):
        for field in ('dividends', 'ohlc'):
            with self.subTest(field=field), TemporaryDirectory() as directory:
                source, database = self.create_inputs(Path(directory))
                self.add_versioned_policy(source, database)
                result = replay(source, database)
                self.assertFalse(result['可用于实盘'])
                with closing(sqlite3.connect(database)) as connection, connection:
                    if field == 'dividends':
                        connection.execute('UPDATE cn_daily SET dividends=1')
                    else:
                        # Keeping adjusted_close unchanged preserves adjusted OHLC.
                        connection.execute(
                            'UPDATE cn_daily SET open=open*2, high=high*2, low=low*2, close=close*2',
                        )
                with self.assertRaisesRegex(DifferencingError, 'digest'):
                    replay(source, database)

    def test_unknown_price_contract_cannot_be_replayed(self):
        with TemporaryDirectory() as directory:
            source, database = self.create_inputs(Path(directory))
            data = json.loads(source.read_text(encoding='utf-8'))
            data['price_contract'] = {'version': 'unknown'}
            source.write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaisesRegex(DifferencingError, 'price contract'):
                replay(source, database)
            self.assertFalse(audit(source, database)['声明口径一致'])

    def test_loader_audit_and_replay_agree_on_all_three_fingerprints(self):
        with TemporaryDirectory() as directory:
            source, database = self.create_inputs(Path(directory))
            with closing(sqlite3.connect(database)) as connection, connection:
                connection.executescript('''
                    ALTER TABLE cn_tickers ADD COLUMN name TEXT;
                    ALTER TABLE cn_tickers ADD COLUMN exchange TEXT DEFAULT 'SSE';
                    ALTER TABLE cn_tickers ADD COLUMN is_etf INTEGER DEFAULT 0;
                ''')
            _, _, provenance = load_fractional_database(
                database, ForecastConfig(
                    train_start=date(2024, 1, 1), validation_start=date(2024, 6, 1),
                    test_start=date(2025, 1, 1), test_end=date(2025, 1, 4),
                ), universe_size=2,
            )
            data = json.loads(source.read_text(encoding='utf-8'))
            data['price_contract'] = research_price_contract()
            data['data_provenance'] = provenance
            source.write_text(json.dumps(data), encoding='utf-8')
            report = audit(source, database)
            self.assertTrue(report['研究行情与历史结果一致'])
            self.assertTrue(all(v is True for v in report['指纹核验'].values()))
            self.assertEqual(replay(source, database)['来源口径状态'], '版本化研究口径')

    def test_audit_detects_non_cent_prices_without_certifying_nominal_data(self):
        with TemporaryDirectory() as directory:
            source, database = self.create_inputs(Path(directory))
            before = database.read_bytes()
            report = audit(source, database)
            self.assertTrue(report['研究行情与历史结果一致'])
            self.assertFalse(report['可用于实盘'])
            self.assertEqual(report['股票明细'][1]['非分币OHLC行数'], 4)
            self.assertIsNone(report['指纹核验']['公司行动SHA256'])
            self.assertEqual(database.read_bytes(), before)

    def test_audit_exposes_action_changes_even_if_adjusted_prices_match(self):
        with TemporaryDirectory() as directory:
            source, database = self.create_inputs(Path(directory))
            self.add_versioned_policy(source, database)
            with closing(sqlite3.connect(database)) as connection, connection:
                connection.execute('UPDATE cn_daily SET splits=2')
            report = audit(source, database)
            self.assertFalse(report['研究行情与历史结果一致'])
            self.assertFalse(report['指纹核验']['公司行动SHA256'])
