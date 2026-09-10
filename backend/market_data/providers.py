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
    CRYPTO = 'CRYPTO'


class MarketDataError(RuntimeError):
    """行情源不可用、返回数据无效或标的不存在时的统一异常。"""

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
        """返回当前价相对昨收的绝对变动。"""
        return self.price - self.previous_close

    @property
    def change_percent(self) -> float:
        """返回相对昨收的百分比变动，昨收为零时返回 0。"""
        if not self.previous_close:
            return 0.0
        return self.change / self.previous_close * 100

    def to_dict(self) -> dict[str, Any]:
        """生成可直接返回给 API/前端的 JSON 友好行情字典。"""
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
        """将日期转换为 ISO 字符串，生成 API 友好的 K 线字典。"""
        data = asdict(self)
        data['date'] = self.date.isoformat()
        return data


class MarketDataProvider(ABC):
    """所有市场行情实现必须遵循的统一查询接口。"""

    market: Market

    @abstractmethod
    def get_quote(self, symbol: str) -> Quote:
        raise NotImplementedError

    def get_quotes(self, symbols: list[str]) -> list[Quote]:
        """按输入顺序逐个获取行情；单个失败会中断本批请求。"""
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
        """读取并短暂缓存 A 股实时快照，主数据源失败时切换备用源。"""
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
        """获取 A 股实时行情，并统一为六位代码和人民币计价。"""
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
        """获取 A 股前复权日线历史数据。"""
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
        """从 Yahoo Finance 的 chart 接口获取美股实时行情。"""
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
        """获取指定日期范围内的美股日线历史数据。"""
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


class BinanceProvider(MarketDataProvider):
    """Binance 公共现货行情，读取行情不需要 API 密钥。"""

    market = Market.CRYPTO
    ticker_endpoint = 'https://api.binance.com/api/v3/ticker/24hr'
    klines_endpoint = 'https://api.binance.com/api/v3/klines'

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """移除分隔符并统一为 Binance 使用的大写交易对格式。"""
        return symbol.strip().upper().replace('-', '').replace('/', '')

    def get_quote(self, symbol: str) -> Quote:
        """获取 Binance 现货 24 小时行情，不需要 API 密钥。"""
        normalized = self._normalize_symbol(symbol)
        try:
            response = self.session.get(
                self.ticker_endpoint,
                params={'symbol': normalized},
                headers={'User-Agent': 'stock-research-platform/1.0'},
                timeout=8,
            )
            response.raise_for_status()
            item = response.json()
            close = float(item['lastPrice'])
            timestamp = datetime.fromtimestamp(int(item['closeTime']) / 1000, timezone.utc)
            return Quote(
                symbol=normalized,
                market=self.market,
                name=normalized,
                price=close,
                previous_close=float(item['prevClosePrice']),
                open=float(item['openPrice']),
                high=float(item['highPrice']),
                low=float(item['lowPrice']),
                volume=int(float(item['volume'])),
                currency='USDT',
                timestamp=timestamp,
                source='binance',
            )
        except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
            raise MarketDataError(f'加密货币行情获取失败: {exc}') from exc

    def get_history(self, symbol: str, start: date, end: date) -> list[HistoricalBar]:
        """获取 Binance 日线 K 线，并转换为统一的历史柱格式。"""
        normalized = self._normalize_symbol(symbol)
        try:
            response = self.session.get(
                self.klines_endpoint,
                params={
                    'symbol': normalized,
                    'interval': '1d',
                    'startTime': int(datetime.combine(start, time.min, timezone.utc).timestamp() * 1000),
                    'endTime': int(datetime.combine(end, time.max, timezone.utc).timestamp() * 1000),
                    'limit': 1000,
                },
                headers={'User-Agent': 'stock-research-platform/1.0'},
                timeout=8,
            )
            response.raise_for_status()
            return [HistoricalBar(
                date=datetime.fromtimestamp(int(item[0]) / 1000, timezone.utc).date(),
                open=float(item[1]),
                high=float(item[2]),
                low=float(item[3]),
                close=float(item[4]),
                volume=int(float(item[5])),
            ) for item in response.json()]
        except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
            raise MarketDataError(f'加密货币历史行情获取失败: {exc}') from exc


@lru_cache(maxsize=3)
def get_provider(market: Market | str) -> MarketDataProvider:
    """按市场返回可复用的行情 provider 实例，最多缓存三个市场。"""
    try:
        normalized = Market(str(market).upper())
    except ValueError as exc:
        raise MarketDataError(f'不支持的市场: {market}') from exc
    if normalized == Market.A_SHARE:
        return AShareProvider()
    if normalized == Market.US:
        return YahooFinanceProvider()
    return BinanceProvider()