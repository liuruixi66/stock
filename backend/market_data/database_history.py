from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from django.conf import settings

from .local_history import _validate_bars, normalize_symbol
from .providers import HistoricalBar, Market, MarketDataError
from .price_basis import ADJUSTED_BASIS, adjusted_ohlc


class SQLiteHistoryProvider:
    """从配置的 stocks SQLite 数据库读取复权日线行情。

    A 股和美股分别读取 `cn_daily`、`us_daily` 表；A 股代码会先映射为数据库内部
    标识。读取采用只读连接，并用复权收盘价相对原始收盘价的比例调整 OHLC，
    使研究流程能够统一使用复权价格。
    """

    def __init__(self, market: Market | str, database_path: Path | str | None = None) -> None:
        try:
            self.market = Market(str(market).upper())
        except ValueError as exc:
            raise MarketDataError(f'Unsupported market: {market}') from exc
        if self.market not in (Market.A_SHARE, Market.US):
            raise MarketDataError('The stocks database supports A and US markets only')
        self.database_path = Path(
            database_path if database_path is not None else settings.STOCKS_DATABASE_PATH,
        )
        self.datasets: dict[str, dict] = {}

    def _database_symbol(self, connection: sqlite3.Connection, normalized: str) -> str:
        if self.market == Market.US:
            return normalized
        row = connection.execute(
            'SELECT symbol FROM cn_tickers WHERE code = ? OR symbol = ? LIMIT 1',
            (normalized, normalized),
        ).fetchone()
        if row is None:
            raise MarketDataError(f'Stock not found in database: {normalized}')
        return str(row[0])

    def get_history(self, symbol: str, start: date, end: date) -> list[HistoricalBar]:
        if start > end:
            raise MarketDataError('Start date must not exceed end date')
        normalized = normalize_symbol(self.market, symbol)
        if not self.database_path.is_file():
            raise MarketDataError(f'Stocks database not found: {self.database_path}')

        table = 'cn_daily' if self.market == Market.A_SHARE else 'us_daily'
        try:
            uri = f'{self.database_path.resolve().as_uri()}?mode=ro'
            connection = sqlite3.connect(uri, uri=True)
            try:
                database_symbol = self._database_symbol(connection, normalized)
                rows = connection.execute(
                    f'''
                    SELECT date, open, high, low, close, adj_close, volume
                    FROM {table}
                    WHERE symbol = ? AND date >= ? AND date <= ?
                    ORDER BY date
                    ''',
                    (database_symbol, start.isoformat(), end.isoformat()),
                ).fetchall()
            finally:
                connection.close()
        except sqlite3.Error as exc:
            raise MarketDataError(f'Unable to read stocks database: {exc}') from exc

        if not rows:
            raise MarketDataError(
                f'No database bars for {normalized} between {start} and {end}',
            )

        bars = []
        try:
            for day, open_price, high, low, close, adjusted_close, volume in rows:
                adjusted_open, adjusted_high, adjusted_low, adjusted_last = adjusted_ohlc(
                    open_price, high, low, close, adjusted_close,
                )
                bars.append(HistoricalBar(
                    date=date.fromisoformat(day),
                    open=adjusted_open, high=adjusted_high, low=adjusted_low,
                    close=adjusted_last,
                    volume=int(volume),
                ))
            _validate_bars(bars, start, end)
        except (TypeError, ValueError, OverflowError) as exc:
            raise MarketDataError(f'Invalid database bars for {normalized}: {exc}') from exc

        self.datasets[normalized] = {
            'source': 'stocks.db',
            'table': table,
            'symbol': database_symbol,
            'adjustment': 'adjusted close factor applied to OHLC',
            'price_basis': ADJUSTED_BASIS,
            'nominal_prices_verified': False,
            'point_in_time_verified': False,
            'requested_start': start.isoformat(),
            'requested_end': end.isoformat(),
            'first_bar': bars[0].date.isoformat(),
            'last_bar': bars[-1].date.isoformat(),
            'bar_count': len(bars),
            'missing_adjusted_close_count': 0,
        }
        return bars
