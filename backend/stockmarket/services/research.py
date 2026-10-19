"""研究与回测应用服务。

本层负责选择历史数据源、调用纯研究算法并保存应留档的研究结果；算法规则位于
`research`，数据读取位于 `market_data`，API 视图不需要直接依赖两者的内部实现。
"""

from datetime import date

from market_data import MarketDataError
from market_data.database_history import SQLiteHistoryProvider
from market_data.local_history import LocalHistoryProvider, RESEARCH_START, available_end
from research.quant_research import (
    run_leaky_integrator_experiment,
    run_portfolio_baseline,
    run_sma_cross,
)
from stockmarket.models import ResearchRun


def default_research_range() -> tuple[date, date]:
    """返回研究页面默认日期区间，结束日采用本地快照实际可用的最新日期。"""
    return RESEARCH_START, available_end()


def _history_provider(market: str, data_source: str):
    """根据请求的来源选择本地快照或只读 SQLite 行情库。"""
    if data_source == 'snapshot':
        return LocalHistoryProvider(market)
    if data_source == 'database':
        return SQLiteHistoryProvider(market)
    raise MarketDataError(f'Unsupported research data source: {data_source}')


def run_sma_research(
    *,
    market: str,
    symbol: str,
    start: date,
    end: date,
    data_source: str = 'snapshot',
    initial_cash: float = 100000,
    short_window: int = 5,
    long_window: int = 20,
    commission_rate: float = 0.0003,
    slippage_bps: float = 2,
) -> dict:
    """执行单标的均线回测并持久化摘要、参数和成交记录。"""
    provider = _history_provider(market, data_source)
    bars = provider.get_history(symbol, start, end)
    result = run_sma_cross(
        bars=bars,
        initial_cash=initial_cash,
        short_window=short_window,
        long_window=long_window,
        commission_rate=commission_rate,
        slippage_bps=slippage_bps,
    )
    normalized_market = market.upper()
    normalized_symbol = symbol.upper()
    result.update({
        'symbol': normalized_symbol,
        'market': normalized_market,
        'data_source': provider.__class__.__name__,
        'datasets': provider.datasets,
        'historical_data': [bar.to_dict() for bar in bars],
    })
    run = ResearchRun.objects.create(
        market=normalized_market,
        symbol=normalized_symbol,
        strategy='sma_cross',
        parameters={
            'short_window': short_window,
            'long_window': long_window,
            'initial_cash': initial_cash,
            'commission_rate': commission_rate,
            'slippage_bps': slippage_bps,
            'data_source': data_source,
            'datasets': provider.datasets,
        },
        start_date=start,
        end_date=end,
        total_return=result['total_return'],
        max_drawdown=result['max_drawdown'],
        sharpe_ratio=result['sharpe_ratio'],
        trade_count=result['trade_count'],
        trades=result['trades'],
    )
    result['run_id'] = run.id
    return result


def run_portfolio_research(
    *,
    market: str,
    symbols: list[str],
    start: date,
    end: date,
    data_source: str = 'snapshot',
    initial_cash: float = 100000,
    strategy: str = 'equal_weight',
    lookback: int | None = None,
    transaction_cost_bps: float = 2,
    entropy_strength: float = 0,
    impact_bps: float = 0,
    impact_exponent: float = 1,
) -> dict:
    """加载组合标的历史数据并执行统一的组合基准算法。"""
    provider = _history_provider(market, data_source)
    bars_by_symbol = {
        symbol: provider.get_history(symbol, start, end)
        for symbol in symbols
    }
    result = run_portfolio_baseline(
        bars_by_symbol=bars_by_symbol,
        initial_cash=initial_cash,
        strategy=strategy,
        lookback=lookback,
        transaction_cost_bps=transaction_cost_bps,
        entropy_strength=entropy_strength,
        impact_bps=impact_bps,
        impact_exponent=impact_exponent,
    )
    result.update({
        'market': market,
        'data_source': provider.__class__.__name__,
        'datasets': provider.datasets,
        'data_counts': {symbol: len(bars) for symbol, bars in bars_by_symbol.items()},
        'start_date': start.isoformat(),
        'end_date': end.isoformat(),
    })
    return result


def run_leaky_forecast_research(
    *,
    market: str,
    symbol: str,
    start: date,
    end: date,
    data_source: str = 'snapshot',
    train_window: int = 20,
    horizon: int = 20,
    gamma_values: list[float] | None = None,
) -> dict:
    """加载单标的历史行情并运行递归差分预测误差实验。"""
    provider = _history_provider(market, data_source)
    bars = provider.get_history(symbol, start, end)
    result = run_leaky_integrator_experiment(
        bars=bars,
        train_window=train_window,
        horizon=horizon,
        gamma_values=gamma_values,
    )
    result.update({
        'market': market,
        'symbol': symbol,
        'data_source': provider.__class__.__name__,
        'datasets': provider.datasets,
        'data_count': len(bars),
        'start_date': start.isoformat(),
        'end_date': end.isoformat(),
    })
    return result
