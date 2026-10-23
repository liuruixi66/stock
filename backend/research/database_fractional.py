from __future__ import annotations

from datetime import date
import json
import logging
from pathlib import Path
import random
import re
import sqlite3
from time import monotonic

import pandas as pd

from research.fractional_forecast import (
    DatabaseRandomUniverse, DifferencingError, ForecastConfig, validate_prices,
)
from market_data.price_basis import (
    ACTION_COLUMNS, ADJUSTED_BASIS, PRICE_COLUMNS, adjusted_ohlc,
    frame_digest, research_price_contract,
)

logger = logging.getLogger(__name__)


def load_fractional_database(
    database_path: Path | str, config: ForecastConfig, seed: int = 42,
    universe_size: int = 30,
) -> tuple[pd.DataFrame, DatabaseRandomUniverse, dict]:
    """从 stocks.db 中抽取可复现的沪市股票样本及完整行情。

    先只读扫描数据库，筛出覆盖训练、验证和测试期间且测试数据完整的股票，
    再依据固定随机种子抽样。返回的样本清单会记录入选股票与筛选元数据，
    便于复现实验；它仍是按当前数据库构造的研究样本，不代表历史时点真实成分。
    """
    config.validate()
    if (isinstance(seed, bool) or not isinstance(seed, int) or seed < 0
            or isinstance(universe_size, bool) or not isinstance(universe_size, int)
            or universe_size < 1):
        raise DifferencingError('Seed must be nonnegative and universe size must be positive')

    path = Path(database_path).expanduser().resolve()
    if not path.is_file():
        raise DifferencingError(f'Stocks database not found: {path}')

    uri = f'{path.as_uri()}?mode=ro'
    started = monotonic()
    last_report = started
    phase = 'Checking complete-history stock eligibility'

    def report_query_progress() -> int:
        nonlocal last_report
        now = monotonic()
        if now - last_report >= 10:
            logger.info('%s: SQLite query still running (%.0fs elapsed)', phase, now - started)
            last_report = now
        return 0

    logger.info('Reading database read-only: %s', path)
    logger.info('%s; this scans historical prices before GPU training starts', phase)
    try:
        connection = sqlite3.connect(uri, uri=True)
        try:
            connection.execute('BEGIN')
            connection.set_progress_handler(report_query_progress, 100000)
            candidates = connection.execute(
                '''
                WITH market_days AS (
                    SELECT
                        COUNT(DISTINCT CASE
                            WHEN d.date BETWEEN ? AND ? THEN d.date
                        END) AS day_count,
                        MIN(d.date) AS first_training_day,
                        MAX(CASE WHEN d.date BETWEEN ? AND ? THEN d.date END)
                            AS last_test_day
                    FROM cn_daily AS d
                    JOIN cn_tickers AS t ON t.symbol = d.symbol
                    WHERE t.exchange = 'SSE' AND COALESCE(t.is_etf, 0) = 0
                      AND d.date BETWEEN ? AND ?
                ),
                stock_coverage AS (
                    SELECT t.symbol, t.code, t.name,
                           MIN(d.date) AS first_date, MAX(d.date) AS last_date,
                           SUM(CASE WHEN d.date BETWEEN ? AND ? THEN 1 ELSE 0 END)
                               AS test_rows,
                           SUM(CASE WHEN d.date BETWEEN ? AND ? AND (
                               d.volume IS NULL OR d.volume < 0 OR d.adj_close IS NULL
                               OR d.adj_close <= 0
                           ) THEN 1 ELSE 0 END) AS invalid_test_rows,
                           SUM(CASE WHEN d.open IS NULL OR d.open <= 0
                               OR d.high IS NULL OR d.high <= 0
                               OR d.low IS NULL OR d.low <= 0
                               OR d.close IS NULL OR d.close <= 0
                               OR d.volume IS NULL OR d.volume < 0
                               OR d.adj_close IS NULL OR d.adj_close <= 0
                               OR d.low > MIN(d.open, d.close)
                               OR d.high < MAX(d.open, d.close)
                               THEN 1 ELSE 0 END) AS invalid_rows
                    FROM cn_daily AS d
                    JOIN cn_tickers AS t ON t.symbol = d.symbol
                    WHERE t.exchange = 'SSE' AND COALESCE(t.is_etf, 0) = 0
                      AND t.code GLOB '[0-9][0-9][0-9][0-9][0-9][0-9]'
                      AND d.date BETWEEN ? AND ?
                    GROUP BY t.symbol, t.code, t.name
                )
                SELECT symbol, code, name
                FROM stock_coverage
                WHERE first_date <= (SELECT first_training_day FROM market_days)
                  AND last_date >= (SELECT last_test_day FROM market_days)
                  AND test_rows = (SELECT day_count FROM market_days)
                  AND invalid_test_rows = 0 AND invalid_rows = 0
                ORDER BY code
                ''',
                (
                    config.test_start.isoformat(), config.test_end.isoformat(),
                    config.test_start.isoformat(), config.test_end.isoformat(),
                    config.train_start.isoformat(), config.test_end.isoformat(),
                    config.test_start.isoformat(), config.test_end.isoformat(),
                    config.test_start.isoformat(), config.test_end.isoformat(),
                    config.train_start.isoformat(), config.test_end.isoformat(),
                ),
            ).fetchall()
            eligible = [
                (str(symbol), str(code).zfill(6), str(name or ''))
                for symbol, code, name in candidates
                if re.fullmatch(r'\d{6}', str(code).zfill(6))
            ]
            if len(eligible) < universe_size:
                raise DifferencingError(
                    f'Only {len(eligible)} database stocks have complete adjusted history '
                    f'for the requested period; {universe_size} are required',
                )

            selected = sorted(random.Random(seed).sample(eligible, universe_size))
            logger.info('Found %d eligible stocks; selected %d with seed %d',
                        len(eligible), len(selected), seed)
            phase = 'Loading selected stock prices'
            logger.info('%s', phase)
            symbols = [symbol for symbol, _, _ in selected]
            placeholders = ','.join('?' for _ in symbols)
            rows = connection.execute(
                f'''
                SELECT t.code, d.date, d.open, d.high, d.low, d.close,
                       d.adj_close, d.volume, d.dividends, d.splits
                FROM cn_daily AS d
                JOIN cn_tickers AS t ON t.symbol = d.symbol
                WHERE t.symbol IN ({placeholders}) AND d.date BETWEEN ? AND ?
                ORDER BY t.code, d.date
                ''',
                [*symbols, config.train_start.isoformat(), config.test_end.isoformat()],
            ).fetchall()
        finally:
            connection.close()
    except sqlite3.Error as exc:
        raise DifferencingError(f'Unable to read stocks database: {exc}') from exc

    records = []
    logger.info('Adjusting and validating %d price rows', len(rows))
    vendor_records = []
    for code, day, open_price, high, low, close, adjusted_close, volume, dividends, splits in rows:
        try:
            adjusted_open, adjusted_high, adjusted_low, adjusted_last = adjusted_ohlc(
                open_price, high, low, close, adjusted_close,
            )
        except ValueError as exc:
            raise DifferencingError(f'Invalid adjustment for {code} on {day}: {exc}') from exc
        vendor_records.append({
            'date': date.fromisoformat(day), 'instrument': f'{code}.SH',
            'open': float(open_price), 'high': float(high), 'low': float(low),
            'close': float(close), 'volume': float(volume),
            'dividends': dividends, 'splits': splits,
        })
        records.append({
            'date': day,
            'instrument': f'{str(code).zfill(6)}.SH',
            'open': adjusted_open, 'high': adjusted_high,
            'low': adjusted_low, 'close': adjusted_last,
            'volume': float(volume),
        })
    prices = validate_prices(pd.DataFrame.from_records(records))
    prices.attrs['price_basis'] = ADJUSTED_BASIS
    vendor_frame = pd.DataFrame.from_records(vendor_records)

    selected_codes = [f'{code}.SH' for _, code, _ in selected]
    universe = DatabaseRandomUniverse(
        selected_codes, date.today(), seed, len(eligible),
    )
    price_digest = frame_digest(prices, PRICE_COLUMNS)
    metadata = {
        'source': 'stocks.db',
        'database_path': str(path),
        'table': 'cn_daily',
        'ticker_table': 'cn_tickers',
        'exchange': 'SSE',
        'adjustment': 'adj_close / close factor applied to OHLC',
        'price_contract': research_price_contract(),
        'vendor_ohlc_sha256': frame_digest(vendor_frame, PRICE_COLUMNS),
        'corporate_actions_sha256': frame_digest(vendor_frame, ACTION_COLUMNS),
        'universe_mode': 'seeded random sample of complete-history Shanghai non-ETF stocks',
        'universe_selection_date': universe.selection_date.isoformat(),
        'universe_seed': seed,
        'universe_size': universe_size,
        'eligible_universe_size': len(eligible),
        'selected_instruments': selected_codes,
        'train_start': config.train_start.isoformat(),
        'test_end': config.test_end.isoformat(),
        'price_rows': len(prices),
        'selected_prices_sha256': price_digest,
        'survivorship_bias': True,
    }
    logger.info('Database ready: %d stocks, %d rows, %.1fs elapsed',
                len(selected), len(prices), monotonic() - started)
    return prices, universe, metadata
