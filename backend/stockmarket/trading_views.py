import json
from decimal import Decimal, InvalidOperation

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from market_data import MarketDataError, get_provider
from .models import SimulationAccount, SimulationOrder
from .paper_trading import TradingError, create_account, submit_order


def _account_data(account: SimulationAccount) -> dict:
    return {
        'id': account.id,
        'name': account.name,
        'market': account.market,
        'currency': account.currency,
        'initial_cash': float(account.initial_cash),
        'cash': float(account.cash),
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
        )
        return JsonResponse({'success': True, 'data': _account_data(account)}, status=201)
    except (ValueError, InvalidOperation, TradingError) as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)


@csrf_exempt
def orders(request):
    if request.method == 'GET':
        queryset = SimulationOrder.objects.select_related('account')
        if request.GET.get('account_id'):
            queryset = queryset.filter(account_id=request.GET['account_id'])
        data = [{
            'id': item.id,
            'account_id': item.account_id,
            'symbol': item.symbol,
            'side': item.side,
            'order_type': item.order_type,
            'quantity': item.quantity,
            'requested_price': float(item.requested_price) if item.requested_price is not None else None,
            'executed_price': float(item.executed_price) if item.executed_price is not None else None,
            'commission': float(item.commission),
            'tax': float(item.tax),
            'status': item.status,
            'message': item.message,
            'created_at': item.created_at.isoformat(),
        } for item in queryset[:200]]
        return JsonResponse({'success': True, 'data': data})
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '不支持的请求方法'}, status=405)
    try:
        data = json.loads(request.body or '{}')
        order = submit_order(
            account_id=int(data['account_id']),
            symbol=data['symbol'],
            side=data['side'],
            quantity=int(data['quantity']),
            order_type=data.get('order_type', 'MARKET'),
            requested_price=Decimal(str(data['price'])) if data.get('price') is not None else None,
        )
        return JsonResponse({'success': order.status != 'REJECTED', 'data': {'id': order.id, 'status': order.status, 'message': order.message}}, status=201)
    except (KeyError, ValueError, InvalidOperation, TradingError, SimulationAccount.DoesNotExist) as exc:
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)


def account_summary(request, account_id: int):
    try:
        account = SimulationAccount.objects.get(pk=account_id)
    except SimulationAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': '账户不存在'}, status=404)
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
        'total_return': float((total_assets / account.initial_cash - 1) * 100),
        'positions': positions,
    }})