from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timezone
from enum import StrEnum
from functools import lru_cache
from importlib import import_module
from time import monotonic
from typing import Any

import requests


class Market(StrEnum):
    A_SHARE = 'A'
    US = 'US'


class MarketDataError(RuntimeError):
    pass


@dataclass(frozen=True)
class Quote:
    symbol: str
    market: Market
    name: str
    price: float
    previous_close: float
    open: float
    high: float
    low: float
    volume: int
    currency: str
    timestamp: datetime
    source: str

    @property
    def change(self) -> float:
        return self.price - self.previous_close

    @property
    def change_percent(self) -> float:
        if not self.previous_close:
            return 0.0
        return self.change / self.previous_close * 100

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data['market'] = self.market.value
        data['timestamp'] = self.timestamp.isoformat()
        data['change'] = round(self.change, 4)
        data['change_percent'] = round(self.change_percent, 4)
        return data


@dataclass(frozen=True)
class HistoricalBar:
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data['date'] = self.date.isoformat()
        return data


class MarketDataProvider(ABC):
    market: Market

    @abstractmethod
    def get_quote(self, symbol: str) -> Quote:
        raise NotImplementedError

    def get_quotes(self, symbols: list[str]) -> list[Quote]:
        return [self.get_quote(symbol) for symbol in symbols]

    @abstractmethod
    def get_history(self, symbol: str, start: date, end: date) -> list[HistoricalBar]:
        raise NotImplementedError


class AShareProvider(MarketDataProvider):
    market = Market.A_SHARE

    def __init__(self) -> None:
        self._spot_frame = None
        self._spot_loaded_at = 0.0
        self._spot_source = 'akshare/eastmoney'

    def _get_spot_frame(self):
        if self._spot_frame is None or monotonic() - self._spot_loaded_at > 10:
            ak = import_module('akshare')

            try:
                self._spot_frame = ak.stock_zh_a_spot_em()
                self._spot_source = 'akshare/eastmoney'
            except Exception:
                self._spot_frame = ak.stock_zh_a_spot()
                self._spot_source = 'akshare/sina'
            self._spot_loaded_at = monotonic()
        return self._spot_frame

    def get_quote(self, symbol: str) -> Quote:
        normalized = symbol.strip().upper().split('.')[0]
        try:
            spot = self._get_spot_frame()
            codes = spot['代码'].astype(str).str.extract(r'(\d{6})', expand=False)
            row = spot.loc[codes == normalized]
            if row.empty:
                raise MarketDataError(f'未找到A股代码: {symbol}')
            item = row.iloc[0]
            return Quote(
                symbol=normalized,
                market=self.market,
                name=str(item['名称']),
                price=float(item['最新价']),
                previous_close=float(item['昨收']),
                open=float(item['今开']),
                high=float(item['最高']),
                low=float(item['最低']),
                volume=int(float(item['成交量'])),
                currency='CNY',
                timestamp=datetime.now(timezone.utc),
                source=self._spot_source,
            )
        except MarketDataError:
            raise
        except ImportError as exc:
            raise MarketDataError('A股数据源不可用，请安装 akshare') from exc
        except Exception as exc:
            raise MarketDataError(f'A股行情获取失败: {exc}') from exc

    def get_history(self, symbol: str, start: date, end: date) -> list[HistoricalBar]:
        normalized = symbol.strip().upper().split('.')[0]
        try:
            ak = import_module('akshare')

            frame = ak.stock_zh_a_hist(
                symbol=normalized,
                period='daily',
                start_date=start.strftime('%Y%m%d'),
                end_date=end.strftime('%Y%m%d'),
                adjust='qfq',
            )
            return [HistoricalBar(
                date=datetime.strptime(str(row['日期'])[:10], '%Y-%m-%d').date(),
                open=float(row['开盘']),
                high=float(row['最高']),
                low=float(row['最低']),
                close=float(row['收盘']),
                volume=int(float(row['成交量'])),
            ) for _, row in frame.iterrows()]
        except ImportError as exc:
            raise MarketDataError('A股数据源不可用，请安装 akshare') from exc
        except Exception as exc:
            raise MarketDataError(f'A股历史行情获取失败: {exc}') from exc


class YahooFinanceProvider(MarketDataProvider):
    market = Market.US
    endpoint = 'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}'

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()

    def get_quote(self, symbol: str) -> Quote:
        normalized = symbol.strip().upper()
        try:
            response = self.session.get(
                self.endpoint.format(symbol=normalized),
                params={'interval': '1m', 'range': '1d'},
                headers={'User-Agent': 'stock-research-platform/1.0'},
                timeout=8,
            )
            response.raise_for_status()
            result = response.json()['chart']['result'][0]
            meta = result['meta']
            price = meta.get('regularMarketPrice')
            if price is None:
                raise MarketDataError(f'未找到美股代码: {symbol}')
            timestamp = meta.get('regularMarketTime')
            return Quote(
                symbol=normalized,
                market=self.market,
                name=meta.get('longName') or meta.get('shortName') or normalized,
                price=float(price),
                previous_close=float(meta.get('chartPreviousClose') or meta.get('previousClose') or price),
                open=float(meta.get('regularMarketOpen') or price),
                high=float(meta.get('regularMarketDayHigh') or price),
                low=float(meta.get('regularMarketDayLow') or price),
                volume=int(meta.get('regularMarketVolume') or 0),
                currency=meta.get('currency', 'USD'),
                timestamp=datetime.fromtimestamp(timestamp, timezone.utc) if timestamp else datetime.now(timezone.utc),
                source='yahoo-finance',
            )
        except MarketDataError:
            raise
        except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
            raise MarketDataError(f'美股行情获取失败: {exc}') from exc

    def get_history(self, symbol: str, start: date, end: date) -> list[HistoricalBar]:
        normalized = symbol.strip().upper()
        try:
            response = self.session.get(
                self.endpoint.format(symbol=normalized),
                params={
                    'interval': '1d',
                    'period1': int(datetime.combine(start, time.min, timezone.utc).timestamp()),
                    'period2': int(datetime.combine(end, time.max, timezone.utc).timestamp()),
                },
                headers={'User-Agent': 'stock-research-platform/1.0'},
                timeout=8,
            )
            response.raise_for_status()
            result = response.json()['chart']['result'][0]
            timestamps = result['timestamp']
            values = result['indicators']['quote'][0]
            bars = []
            for index, timestamp in enumerate(timestamps):
                if values['close'][index] is None:
                    continue
                bars.append(HistoricalBar(
                    date=datetime.fromtimestamp(timestamp, timezone.utc).date(),
                    open=float(values['open'][index]),
                    high=float(values['high'][index]),
                    low=float(values['low'][index]),
                    close=float(values['close'][index]),
                    volume=int(values['volume'][index] or 0),
                ))
            return bars
        except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
            raise MarketDataError(f'美股历史行情获取失败: {exc}') from exc


@lru_cache(maxsize=2)
def get_provider(market: Market | str) -> MarketDataProvider:
    try:
        normalized = Market(str(market).upper())
    except ValueError as exc:
        raise MarketDataError(f'不支持的市场: {market}') from exc
    if normalized == Market.A_SHARE:
        return AShareProvider()
    return YahooFinanceProvider()