from __future__ import annotations

import hashlib
import json
import math
import os
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

from django.conf import settings

from .providers import HistoricalBar, Market, MarketDataError, get_provider


RESEARCH_START = date(2024, 1, 1)
RESEARCH_END = date(2026, 9, 21)
RESEARCH_UNIVERSE = {
    'A': ['000001', '600519', '601318', '600036', '000333', '300750', '600900', '601899', '000858', '600276'],
    'US': ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'JPM', 'XOM', 'UNH', 'COST'],
    'CRYPTO': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ZECUSDT'],
}
SOURCE_DETAILS = {
    'A': {'source': 'akshare/eastmoney', 'adjustment': 'qfq', 'timezone': 'Asia/Shanghai', 'volume_unit': 'lot'},
    'US': {'source': 'yahoo-finance', 'adjustment': 'quote OHLC, not dividend-adjusted total return', 'timezone': 'America/New_York', 'volume_unit': 'share'},
    'CRYPTO': {'source': 'binance', 'adjustment': 'none', 'timezone': 'UTC', 'volume_unit': 'base asset, truncated to integer by provider'},
}


def available_end() -> date:
    return min(RESEARCH_END, datetime.now(timezone.utc).date() - timedelta(days=1))


def normalize_symbol(market: Market, symbol: str) -> str:
    normalized = symbol.strip().upper()
    if market == Market.A_SHARE:
        normalized = normalized.split('.')[0]
    elif market == Market.CRYPTO:
        normalized = normalized.replace('/', '').replace('-', '')
    if not re.fullmatch(r'[A-Z0-9][A-Z0-9.^-]{0,31}', normalized):
        raise MarketDataError('Invalid historical data symbol')
    return normalized


def _digest(rows: list[dict]) -> str:
    return hashlib.sha256(json.dumps(rows, sort_keys=True, allow_nan=False).encode()).hexdigest()


def _validate_bars(bars: list[HistoricalBar], start: date, end: date) -> None:
    if not bars:
        raise MarketDataError('Historical dataset is empty')
    dates = [bar.date for bar in bars]
    if dates != sorted(set(dates)):
        raise MarketDataError('Historical dates must be unique and ordered')
    for bar in bars:
        prices = (bar.open, bar.high, bar.low, bar.close)
        if (not start <= bar.date <= end
                or not all(math.isfinite(price) and price > 0 for price in prices)
                or not math.isfinite(bar.volume) or bar.volume < 0
                or not bar.low <= min(bar.open, bar.close) <= max(bar.open, bar.close) <= bar.high):
            raise MarketDataError(f'Invalid historical bar: {bar.date}')


class LocalHistoryProvider:
    def __init__(self, market: Market | str, root: Path | None = None) -> None:
        try:
            self.market = Market(str(market).upper())
        except ValueError as exc:
            raise MarketDataError(f'Unsupported market: {market}') from exc
        self.root = Path(root if root is not None else getattr(
            settings, 'HISTORICAL_DATA_DIR', settings.BASE_DIR / 'data' / 'history' / '2024_2026',
        ))
        self.datasets: dict[str, dict] = {}

    def path(self, symbol: str) -> Path:
        return self.root / self.market.value / f'{normalize_symbol(self.market, symbol)}.json'

    def get_history(self, symbol: str, start: date, end: date) -> list[HistoricalBar]:
        if start > end:
            raise MarketDataError('Start date must not exceed end date')
        normalized = normalize_symbol(self.market, symbol)
        path = self.path(normalized)
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
            metadata, rows = payload['metadata'], payload['bars']
            if (metadata['schema_version'] != 1 or metadata['market'] != self.market.value
                    or metadata['symbol'] != normalized or metadata['sha256'] != _digest(rows)):
                raise MarketDataError(f'Historical snapshot integrity check failed: {path}')
            covered_start = date.fromisoformat(metadata['requested_start'])
            covered_end = date.fromisoformat(metadata['requested_end'])
            if start < covered_start or end > covered_end:
                raise MarketDataError(f'Local snapshot covers {covered_start}..{covered_end}; requested {start}..{end}')
            bars = [HistoricalBar(date=date.fromisoformat(row['date']), **{
                key: row[key] for key in ('open', 'high', 'low', 'close', 'volume')
            }) for row in rows]
            _validate_bars(bars, covered_start, covered_end)
            selected = [bar for bar in bars if start <= bar.date <= end]
            if not selected:
                raise MarketDataError('No local bars in requested date range')
            self.datasets[normalized] = metadata
            return selected
        except FileNotFoundError as exc:
            raise MarketDataError(f'Local history missing: {path}. Run manage.py download_history first; network fallback is disabled.') from exc
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise MarketDataError(f'Invalid local history file: {path}: {exc}') from exc


def download_history(market: str, symbol: str, start: date, end: date, root: Path | None = None) -> dict:
    if start > end or end >= datetime.now(timezone.utc).date():
        raise MarketDataError('Download requires an ordered date range ending before today (UTC)')
    local = LocalHistoryProvider(market, root)
    normalized = normalize_symbol(local.market, symbol)
    path = local.path(normalized)
    if path.exists():
        local.get_history(normalized, start, end)
        return {**local.datasets[normalized], 'cached': True}
    provider = get_provider(local.market)
    if local.market == Market.CRYPTO:
        bars = []
        chunk_start = start
        while chunk_start <= end:
            chunk_end = min(end, chunk_start + timedelta(days=999))
            chunk = provider.get_history(normalized, chunk_start, chunk_end)
            _validate_bars(chunk, chunk_start, chunk_end)
            if len(chunk) != (chunk_end - chunk_start).days + 1:
                raise MarketDataError(f'Incomplete crypto daily history: {normalized}, {chunk_start}..{chunk_end}')
            bars.extend(chunk)
            chunk_start = chunk_end + timedelta(days=1)
    else:
        bars = provider.get_history(normalized, start, end)
    _validate_bars(bars, start, end)
    rows = [bar.to_dict() for bar in bars]
    metadata = {
        'schema_version': 1, 'market': local.market.value, 'symbol': normalized,
        'interval': '1d', 'requested_start': start.isoformat(), 'requested_end': end.isoformat(),
        'first_bar': bars[0].date.isoformat(), 'last_bar': bars[-1].date.isoformat(),
        'bar_count': len(bars), 'downloaded_at': datetime.now(timezone.utc).isoformat(),
        'sha256': _digest(rows), **SOURCE_DETAILS[local.market.value],
    }
    content = json.dumps({'metadata': metadata, 'bars': rows}, indent=2, allow_nan=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as output:
            temporary_path = Path(output.name)
            output.write(content)
        os.link(temporary_path, path)
    except FileExistsError as exc:
        raise MarketDataError(f'Snapshot already exists; refusing overwrite: {path}') from exc
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return {**metadata, 'cached': False}