import json
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from brokers import BrokerError, broker_catalog
from market_data import MarketDataError, get_provider
from market_data.local_history import LocalHistoryProvider, RESEARCH_START, available_end
from .analytics import build_account_analytics
from .models import ResearchRun, SimulationAccount, SimulationOrder, WatchlistItem
from .paper_trading import TradingError, cancel_order, create_account, live_trading_enabled, submit_order, sync_account
from .quant_research import ResearchError, run_leaky_integrator_experiment, run_portfolio_baseline, run_sma_cross


def _account_data(account: SimulationAccount) -> dict:
    return {
        'id': account.id,
        'name': account.name,
        'market': account.market,
        'currency': account.currency,
        'initial_cash': float(account.initial_cash),
        'cash': float(account.cash),
        'broker': account.broker,
        'broker_label': account.get_broker_display(),
        'broker_account_id': account.broker_account_id,
        'trading_mode': account.trading_mode,
        'is_external': account.is_external,
        'last_synced_at': account.last_synced_at.isoformat() if account.last_synced_at else None,
    }


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
        return JsonResponse({'success': True, 'data': [_account_data(item) for item in SimulationAccount.objects.all()]})
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '不支持的请求方法'}, status=405)
    try:
        data = json.loads(request.body or '{}')
        account = create_account(
            data.get('name', '').strip(),
            data.get('market', 'A'),
            Decimal(str(data.get('initial_cash', 100000))),
            broker=str(data.get('broker', 'SIM')),
            broker_account_id=str(data.get('broker_account_id', '') or ''),
            trading_mode=str(data.get('trading_mode', 'PAPER')),
        )
        return JsonResponse({'success': True, 'data': _account_data(account)}, status=201)
    except (ValueError, InvalidOperation, TradingError) as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)


def brokers(request):
    """列出可用券商通道及其 SDK/环境变量要求，供前端建账时选择。"""
    return JsonResponse({'success': True, 'data': {
        'brokers': broker_catalog(),
        'live_trading_enabled': live_trading_enabled(),
    }})


@csrf_exempt
def account_sync(request, account_id: int):
    """从券商拉取资金、持仓和未完成委托，内置模拟账户直接返回。"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '不支持的请求方法'}, status=405)
    try:
        account = SimulationAccount.objects.get(pk=account_id)
    except SimulationAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': '账户不存在'}, status=404)
    try:
        sync_account(account)
    except BrokerError as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=502)
    return JsonResponse({'success': True, 'data': _account_data(account)})


def _order_data(item: SimulationOrder) -> dict:
    return {
        'id': item.id,
        'account_id': item.account_id,
        'symbol': item.symbol,
        'side': item.side,
        'order_type': item.order_type,
        'quantity': item.quantity,
        'filled_quantity': float(item.filled_quantity),
        'requested_price': float(item.requested_price) if item.requested_price is not None else None,
        'executed_price': float(item.executed_price) if item.executed_price is not None else None,
        'amount': float(item.executed_price * item.quantity) if item.executed_price is not None else None,
        'commission': float(item.commission),
        'tax': float(item.tax),
        'status': item.status,
        'broker_order_id': item.broker_order_id,
        'message': item.message,
        'created_at': item.created_at.isoformat(),
    }


@csrf_exempt
def orders(request):
    if request.method == 'GET':
        queryset = SimulationOrder.objects.select_related('account')
        if request.GET.get('account_id'):
            queryset = queryset.filter(account_id=request.GET['account_id'])
        return JsonResponse({'success': True, 'data': [_order_data(item) for item in queryset[:200]]})
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '不支持的请求方法'}, status=405)
    try:
        data = json.loads(request.body or '{}')
        order = submit_order(
            account_id=int(data['account_id']),
            symbol=data['symbol'],
            side=data['side'],
            quantity=Decimal(str(data['quantity'])),
            order_type=data.get('order_type', 'MARKET'),
            requested_price=Decimal(str(data['price'])) if data.get('price') is not None else None,
        )
        return JsonResponse({'success': order.status != 'REJECTED', 'data': _order_data(order)}, status=201)
    except (KeyError, ValueError, InvalidOperation, TradingError, SimulationAccount.DoesNotExist) as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)


@csrf_exempt
def order_cancel(request, order_id: int):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '不支持的请求方法'}, status=405)
    try:
        order = cancel_order(order_id)
    except SimulationOrder.DoesNotExist:
        return JsonResponse({'success': False, 'error': '订单不存在'}, status=404)
    except TradingError as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)
    return JsonResponse({'success': True, 'data': _order_data(order)})


def account_summary(request, account_id: int):
    """返回账户现金、实时持仓市值和总资产；券商账户先尝试同步，失败时返回本地缓存并附带错误。"""
    try:
        account = SimulationAccount.objects.get(pk=account_id)
    except SimulationAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': '账户不存在'}, status=404)
    sync_error = None
    if account.is_external:
        try:
            sync_account(account)
        except BrokerError as exc:
            sync_error = str(exc)
    positions = []
    market_value = Decimal('0')
    provider = get_provider(account.market)
    for position in account.positions.all():
        try:
            quote = provider.get_quote(position.symbol)
            current_price = Decimal(str(quote.price))
        except MarketDataError:
            current_price = position.average_price
        value = current_price * position.quantity
        market_value += value
        positions.append({
            'symbol': position.symbol,
            'quantity': position.quantity,
            'average_price': float(position.average_price),
            'current_price': float(current_price),
            'market_value': float(value),
            'unrealized_pnl': float((current_price - position.average_price) * position.quantity),
        })
    total_assets = account.cash + market_value
    return JsonResponse({'success': True, 'data': {
        **_account_data(account),
        'market_value': float(market_value),
        'total_assets': float(total_assets),
        'total_return': float((total_assets / account.initial_cash - 1) * 100) if account.initial_cash else 0.0,
        'positions': positions,
        'sync_error': sync_error,
    }})


def account_analytics(request, account_id: int):
    """返回账户的 FIFO 已实现盈亏、未实现盈亏及交易统计。"""
    try:
        account = SimulationAccount.objects.get(pk=account_id)
    except SimulationAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': '账户不存在'}, status=404)
    return JsonResponse({'success': True, 'data': build_account_analytics(account)})


@csrf_exempt
def research_backtest(request):
    """执行单标的均线交叉回测，并保存本次研究运行摘要。"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '不支持的请求方法'}, status=405)
    try:
        data = json.loads(request.body or '{}')
        end = date.fromisoformat(data.get('end_date', available_end().isoformat()))
        start = date.fromisoformat(data.get('start_date', RESEARCH_START.isoformat()))
        provider = LocalHistoryProvider(data.get('market', 'A'))
        bars = provider.get_history(data['symbol'], start, end)
        result = run_sma_cross(
            bars=bars,
            initial_cash=float(data.get('initial_cash', 100000)),
            short_window=int(data.get('short_window', 5)),
            long_window=int(data.get('long_window', 20)),
            commission_rate=float(data.get('commission_rate', 0.0003)),
            slippage_bps=float(data.get('slippage_bps', 2)),
        )
        result.update({
            'symbol': data['symbol'].upper(),
            'market': data.get('market', 'A').upper(),
            'data_source': provider.__class__.__name__,
            'datasets': provider.datasets,
            'historical_data': [bar.to_dict() for bar in bars],
        })
        run = ResearchRun.objects.create(
            market=result['market'],
            symbol=result['symbol'],
            strategy='sma_cross',
            parameters={
                'short_window': int(data.get('short_window', 5)),
                'long_window': int(data.get('long_window', 20)),
                'initial_cash': float(data.get('initial_cash', 100000)),
                'commission_rate': float(data.get('commission_rate', 0.0003)),
                'slippage_bps': float(data.get('slippage_bps', 2)),
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
        end = date.fromisoformat(data.get('end_date', available_end().isoformat()))
        start = date.fromisoformat(data.get('start_date', RESEARCH_START.isoformat()))
        if start > end:
            return JsonResponse({'success': False, 'error': '开始日期不能晚于结束日期'}, status=400)
        provider = LocalHistoryProvider(market)
        bars_by_symbol = {
            symbol: provider.get_history(symbol, start, end)
            for symbol in symbols
        }
        result = run_portfolio_baseline(
            bars_by_symbol=bars_by_symbol,
            initial_cash=float(data.get('initial_cash', 100000)),
            strategy=str(data.get('strategy', 'equal_weight')).lower(),
            lookback=int(data['lookback']) if data.get('lookback') is not None else None,
            transaction_cost_bps=float(data.get('transaction_cost_bps', 2)),
            entropy_strength=float(data.get('entropy_strength', 0)),
            impact_bps=float(data.get('impact_bps', 0)),
            impact_exponent=float(data.get('impact_exponent', 1)),
        )
        result.update({
            'market': market,
            'data_source': provider.__class__.__name__,
            'datasets': provider.datasets,
            'data_counts': {symbol: len(bars) for symbol, bars in bars_by_symbol.items()},
            'start_date': start.isoformat(),
            'end_date': end.isoformat(),
        })
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
        end = date.fromisoformat(data.get('end_date', available_end().isoformat()))
        start = date.fromisoformat(data.get('start_date', RESEARCH_START.isoformat()))
        if start > end:
            return JsonResponse({'success': False, 'error': '开始日期不能晚于结束日期'}, status=400)
        raw_gamma_values = data.get('gamma_values') or [1.0, 0.95, 0.9, 0.8]
        if isinstance(raw_gamma_values, str):
            gamma_values = [float(item.strip()) for item in raw_gamma_values.split(',') if item.strip()]
        else:
            gamma_values = [float(item) for item in raw_gamma_values]
        provider = LocalHistoryProvider(market)
        bars = provider.get_history(symbol, start, end)
        result = run_leaky_integrator_experiment(
            bars=bars,
            train_window=int(data.get('train_window', 20)),
            horizon=int(data.get('horizon', 20)),
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