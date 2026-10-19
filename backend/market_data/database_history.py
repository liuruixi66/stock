from __future__ import annotations

import math
import sqlite3
from datetime import date
from pathlib import Path

from django.conf import settings

from .local_history import _validate_bars, normalize_symbol
from .providers import HistoricalBar, Market, MarketDataError


class SQLiteHistoryProvider:
    """Read adjusted daily bars from the configured stocks SQLite database."""

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
        missing_adjustments = 0
        try:
            for day, open_price, high, low, close, adjusted_close, volume in rows:
                raw_close = float(close)
                if adjusted_close is None:
                    adjusted_close = raw_close
                    missing_adjustments += 1
                adjusted_close = float(adjusted_close)
                if not math.isfinite(raw_close) or raw_close <= 0:
                    raise ValueError(f'Invalid close price on {day}')
                factor = adjusted_close / raw_close
                bars.append(HistoricalBar(
                    date=date.fromisoformat(day),
                    open=float(open_price) * factor,
                    high=float(high) * factor,
                    low=float(low) * factor,
                    close=raw_close * factor,
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
            'requested_start': start.isoformat(),
            'requested_end': end.isoformat(),
            'first_bar': bars[0].date.isoformat(),
            'last_bar': bars[-1].date.isoformat(),
            'bar_count': len(bars),
            'missing_adjusted_close_count': missing_adjustments,
        }
        return bars
