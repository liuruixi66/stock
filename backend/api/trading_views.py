"""股票系统 HTTP API 视图。

本模块负责解析 HTTP 参数、校验请求形状并生成 JSON 响应；账户/订单工作流和
研究回测流程通过 `stockmarket.services` 门面调用，行情查询通过 `market_data`
公开接口调用，算法与券商适配细节不在视图中重复实现。
"""

import json
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from brokers import BrokerError
from market_data import MarketDataError, get_provider
from stockmarket.models import ResearchRun
from stockmarket.models import SimulationAccount
from stockmarket.models import SimulationOrder
from stockmarket.models import WatchlistItem
from execution.paper_trading import TradingError
from research.quant_research import ResearchError
from stockmarket.services import (
    account_analytics as build_account_analytics,
    account_data,
    account_summary as build_account_summary,
    cancel_account_order,
    create_trading_account,
    default_research_range,
    order_data,
    place_account_order,
    run_leaky_forecast_research,
    run_portfolio_research,
    run_sma_research,
    sync_trading_account,
    trading_capabilities,
)


def market_quotes(request):
    market = request.GET.get('market', 'A')
    symbols = [item.strip() for item in request.GET.get('symbols', '').split(',') if item.strip()]
    if not symbols or len(symbols) > 20:
        return JsonResponse({'success': False, 'error': '请提供1至20个股票代码'}, status=400)
    try:
        provider = get_provider(market)
        quotes = []
        errors = []
        for symbol in symbols:
            try:
                quotes.append(provider.get_quote(symbol).to_dict())
            except MarketDataError as exc:
                errors.append({'symbol': symbol, 'error': str(exc)})
        return JsonResponse({'success': bool(quotes), 'data': quotes, 'errors': errors})
    except MarketDataError as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)


def market_history(request):
    market = request.GET.get('market', 'A')
    symbol = request.GET.get('symbol', '').strip()
    if not symbol:
        return JsonResponse({'success': False, 'error': '请提供标的代码'}, status=400)
    try:
        end = date.fromisoformat(request.GET.get('end_date', date.today().isoformat()))
        start = date.fromisoformat(
            request.GET.get('start_date', (end - timedelta(days=730)).isoformat())
        )
        if start > end:
            return JsonResponse({'success': False, 'error': '开始日期不能晚于结束日期'}, status=400)
        bars = get_provider(market).get_history(symbol, start, end)
        return JsonResponse({
            'success': True,
            'data': {
                'market': market.upper(),
                'symbol': symbol.upper(),
                'start_date': start.isoformat(),
                'end_date': end.isoformat(),
                'source': get_provider(market).__class__.__name__,
                'bars': [bar.to_dict() for bar in bars],
            },
        })
    except (ValueError, MarketDataError) as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)


def market_minute_data(request):
    """返回只读的已收盘分钟 K 线，不触发任何交易操作。"""
    market = request.GET.get('market', 'CRYPTO').upper()
    symbol = request.GET.get('symbol', '').strip()
    if not symbol:
        return JsonResponse({'success': False, 'error': '请提供标的代码'}, status=400)
    try:
        limit = int(request.GET.get('limit', 500))
        bars = get_provider(market).get_minute_bars(symbol, limit)
        return JsonResponse({
            'success': True,
            'data': {
                'market': market,
                'symbol': symbol.upper(),
                'interval': '1m',
                'source': get_provider(market).__class__.__name__,
                'bars': [bar.to_dict() for bar in bars],
            },
        })
    except (ValueError, MarketDataError) as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)


@csrf_exempt
def accounts(request):
    if request.method == 'GET':
        return JsonResponse({'success': True, 'data': [account_data(item) for item in SimulationAccount.objects.all()]})
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '不支持的请求方法'}, status=405)
    try:
        data = json.loads(request.body or '{}')
        account = create_trading_account(
            data.get('name', '').strip(),
            data.get('market', 'A'),
            Decimal(str(data.get('initial_cash', 100000))),
            broker=str(data.get('broker', 'SIM')),
            broker_account_id=str(data.get('broker_account_id', '') or ''),
            trading_mode=str(data.get('trading_mode', 'PAPER')),
        )
        return JsonResponse({'success': True, 'data': account_data(account)}, status=201)
    except (ValueError, InvalidOperation, TradingError) as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)


def brokers(request):
    """列出可用券商通道及其 SDK/环境变量要求，供前端建账时选择。"""
    return JsonResponse({'success': True, 'data': trading_capabilities()})


@csrf_exempt
def account_sync(request, account_id: int):
    """从券商拉取资金、持仓和未完成委托，内置模拟账户直接返回。"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '不支持的请求方法'}, status=405)
    try:
        account = sync_trading_account(account_id)
    except SimulationAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': '账户不存在'}, status=404)
    except BrokerError as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=502)
    return JsonResponse({'success': True, 'data': account_data(account)})


@csrf_exempt
def orders(request):
    if request.method == 'GET':
        queryset = SimulationOrder.objects.select_related('account')
        if request.GET.get('account_id'):
            queryset = queryset.filter(account_id=request.GET['account_id'])
        return JsonResponse({'success': True, 'data': [order_data(item) for item in queryset[:200]]})
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '不支持的请求方法'}, status=405)
    try:
        data = json.loads(request.body or '{}')
        order = place_account_order(
            account_id=int(data['account_id']),
            symbol=data['symbol'],
            side=data['side'],
            quantity=Decimal(str(data['quantity'])),
            order_type=data.get('order_type', 'MARKET'),
            requested_price=Decimal(str(data['price'])) if data.get('price') is not None else None,
        )
        return JsonResponse({'success': order.status != 'REJECTED', 'data': order_data(order)}, status=201)
    except (KeyError, ValueError, InvalidOperation, TradingError, SimulationAccount.DoesNotExist) as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)


@csrf_exempt
def order_cancel(request, order_id: int):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '不支持的请求方法'}, status=405)
    try:
        order = cancel_account_order(order_id)
    except SimulationOrder.DoesNotExist:
        return JsonResponse({'success': False, 'error': '订单不存在'}, status=404)
    except TradingError as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)
    return JsonResponse({'success': True, 'data': order_data(order)})


def account_summary(request, account_id: int):
    """返回账户现金、实时持仓市值和总资产；券商账户先尝试同步，失败时返回本地缓存并附带错误。"""
    try:
        data = build_account_summary(account_id)
    except SimulationAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': '账户不存在'}, status=404)
    return JsonResponse({'success': True, 'data': data})


def account_analytics(request, account_id: int):
    """返回账户的 FIFO 已实现盈亏、未实现盈亏及交易统计。"""
    try:
        data = build_account_analytics(account_id)
    except SimulationAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': '账户不存在'}, status=404)
    return JsonResponse({'success': True, 'data': data})


@csrf_exempt
def research_backtest(request):
    """执行单标的均线交叉回测，并保存本次研究运行摘要。"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '不支持的请求方法'}, status=405)
    try:
        data = json.loads(request.body or '{}')
        default_start, default_end = default_research_range()
        result = run_sma_research(
            market=data.get('market', 'A'),
            symbol=data['symbol'],
            start=date.fromisoformat(data.get('start_date', default_start.isoformat())),
            end=date.fromisoformat(data.get('end_date', default_end.isoformat())),
            data_source=data.get('data_source', 'snapshot'),
            initial_cash=float(data.get('initial_cash', 100000)),
            short_window=int(data.get('short_window', 5)),
            long_window=int(data.get('long_window', 20)),
            commission_rate=float(data.get('commission_rate', 0.0003)),
            slippage_bps=float(data.get('slippage_bps', 2)),
        )
        return JsonResponse({'success': True, 'data': result})
    except (KeyError, ValueError, ResearchError, MarketDataError) as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)


@csrf_exempt
def portfolio_backtest(request):
    """加载多个标的历史数据并执行组合基准回测。"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '不支持的请求方法'}, status=405)
    try:
        data = json.loads(request.body or '{}')
        market = data.get('market', 'A').upper()
        symbols = data.get('symbols', [])
        if isinstance(symbols, str):
            symbols = [item.strip() for item in symbols.split(',') if item.strip()]
        symbols = [str(symbol).strip().upper() for symbol in symbols if str(symbol).strip()]
        if not symbols or len(symbols) > 20:
            return JsonResponse({'success': False, 'error': '请提供1至20个组合标的'}, status=400)
        default_start, default_end = default_research_range()
        end = date.fromisoformat(data.get('end_date', default_end.isoformat()))
        start = date.fromisoformat(data.get('start_date', default_start.isoformat()))
        if start > end:
            return JsonResponse({'success': False, 'error': '开始日期不能晚于结束日期'}, status=400)
        result = run_portfolio_research(
            market=market,
            symbols=symbols,
            start=start,
            end=end,
            data_source=data.get('data_source', 'snapshot'),
            initial_cash=float(data.get('initial_cash', 100000)),
            strategy=str(data.get('strategy', 'equal_weight')).lower(),
            lookback=int(data['lookback']) if data.get('lookback') is not None else None,
            transaction_cost_bps=float(data.get('transaction_cost_bps', 2)),
            entropy_strength=float(data.get('entropy_strength', 0)),
            impact_bps=float(data.get('impact_bps', 0)),
            impact_exponent=float(data.get('impact_exponent', 1)),
        )
        return JsonResponse({'success': True, 'data': result})
    except (KeyError, TypeError, ValueError, ResearchError, MarketDataError) as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)


@csrf_exempt
def leaky_forecast_experiment(request):
    """执行递归差分预测的 leaky-integrator 误差修正实验。"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '不支持的请求方法'}, status=405)
    try:
        data = json.loads(request.body or '{}')
        market = data.get('market', 'A').upper()
        symbol = str(data.get('symbol', '')).strip().upper()
        if not symbol:
            return JsonResponse({'success': False, 'error': '请提供标的代码'}, status=400)
        default_start, default_end = default_research_range()
        end = date.fromisoformat(data.get('end_date', default_end.isoformat()))
        start = date.fromisoformat(data.get('start_date', default_start.isoformat()))
        if start > end:
            return JsonResponse({'success': False, 'error': '开始日期不能晚于结束日期'}, status=400)
        raw_gamma_values = data.get('gamma_values') or [1.0, 0.95, 0.9, 0.8]
        if isinstance(raw_gamma_values, str):
            gamma_values = [float(item.strip()) for item in raw_gamma_values.split(',') if item.strip()]
        else:
            gamma_values = [float(item) for item in raw_gamma_values]
        result = run_leaky_forecast_research(
            market=market,
            symbol=symbol,
            start=start,
            end=end,
            data_source=data.get('data_source', 'snapshot'),
            train_window=int(data.get('train_window', 20)),
            horizon=int(data.get('horizon', 20)),
            gamma_values=gamma_values,
        )
        return JsonResponse({'success': True, 'data': result})
    except (TypeError, ValueError, ResearchError, MarketDataError) as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)


def _research_run_data(run: ResearchRun) -> dict:
    return {
        'id': run.id,
        'market': run.market,
        'symbol': run.symbol,
        'strategy': run.strategy,
        'parameters': run.parameters,
        'start_date': run.start_date.isoformat(),
        'end_date': run.end_date.isoformat(),
        'total_return': run.total_return,
        'max_drawdown': run.max_drawdown,
        'sharpe_ratio': run.sharpe_ratio,
        'trade_count': run.trade_count,
        'trades': run.trades,
        'created_at': run.created_at.isoformat(),
    }


def research_runs(request):
    queryset = ResearchRun.objects.all()
    if request.GET.get('market'):
        queryset = queryset.filter(market=request.GET['market'].upper())
    if request.GET.get('symbol'):
        queryset = queryset.filter(symbol=request.GET['symbol'].upper())
    return JsonResponse({'success': True, 'data': [_research_run_data(item) for item in queryset[:50]]})


def research_run_detail(request, run_id: int):
    try:
        run = ResearchRun.objects.get(pk=run_id)
    except ResearchRun.DoesNotExist:
        return JsonResponse({'success': False, 'error': '研究记录不存在'}, status=404)
    return JsonResponse({'success': True, 'data': _research_run_data(run)})


@csrf_exempt
def watchlist(request):
    if request.method == 'GET':
        queryset = WatchlistItem.objects.all()
        if request.GET.get('market'):
            queryset = queryset.filter(market=request.GET['market'].upper())
        data = [{
            'id': item.id,
            'market': item.market,
            'symbol': item.symbol,
            'name': item.name,
            'note': item.note,
        } for item in queryset]
        return JsonResponse({'success': True, 'data': data})
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '不支持的请求方法'}, status=405)
    data = json.loads(request.body or '{}')
    market = str(data.get('market', 'A')).upper()
    symbol = str(data.get('symbol', '')).strip().upper()
    if market not in ('A', 'US', 'CRYPTO'):
        return JsonResponse({'success': False, 'error': '市场只支持 A、US 或 CRYPTO'}, status=400)
    if not symbol:
        return JsonResponse({'success': False, 'error': '请填写股票代码'}, status=400)
    item, created = WatchlistItem.objects.get_or_create(
        market=market,
        symbol=symbol,
        defaults={'name': str(data.get('name', '')).strip(), 'note': str(data.get('note', '')).strip()},
    )
    return JsonResponse(
        {'success': True, 'data': {'id': item.id, 'market': item.market, 'symbol': item.symbol, 'name': item.name, 'note': item.note}},
        status=201 if created else 200,
    )


@csrf_exempt
def watchlist_item(request, item_id: int):
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': '不支持的请求方法'}, status=405)
    deleted, _ = WatchlistItem.objects.filter(pk=item_id).delete()
    if not deleted:
        return JsonResponse({'success': False, 'error': '自选股不存在'}, status=404)
    return JsonResponse({'success': True})