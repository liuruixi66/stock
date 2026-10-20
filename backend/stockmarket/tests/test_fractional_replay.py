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


class FractionalReplayTests(SimpleTestCase):
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
            result = replay(source, database, 5)
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
                replay(source, database, 5)
