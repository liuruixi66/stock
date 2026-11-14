"""Limited nominal-share sensitivity analysis, not an exchange fill simulator."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from math import floor, isfinite
from typing import Mapping

import numpy as np
import pandas as pd

from research.fractional_forecast import (
    DatabaseRandomUniverse, DifferencingError, long_only_signal, validate_prices,
)
from market_data.price_basis import ADJUSTED_BASIS, VENDOR_OHLC_BASIS


def money(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def execution_fee(
    notional: float, commission_rate: float, minimum_commission: float,
    transfer_rate: float, stamp_duty_rate: float = 0.0,
) -> dict[str, float]:
    if notional <= 0:
        return {'commission': 0.0, 'transfer_fee': 0.0, 'stamp_duty': 0.0, 'total': 0.0}
    commission = money(max(minimum_commission, notional * commission_rate))
    transfer_fee = money(notional * transfer_rate)
    stamp_duty = money(notional * stamp_duty_rate)
    return {
        'commission': commission, 'transfer_fee': transfer_fee,
        'stamp_duty': stamp_duty,
        'total': money(commission + transfer_fee + stamp_duty),
    }


def simulate_cash_shares(
    prices: pd.DataFrame, predictions: Mapping[tuple[date, str], float],
    universe: DatabaseRandomUniverse, start: date, end: date,
    initial_capital: float = 100000, exposure: float = 0.95,
    buy_cost: float = 0.0005, sell_cost: float = 0.001,
    signal_threshold: float = 0.002, benchmark: bool = False,
    commission_rate: float = 0.0003, minimum_commission: float = 5.0,
    transfer_fee_rate: float = 0.00001, stamp_duty_rate: float = 0.0005,
) -> dict:
    """100-share buys, settled-share sells and a minimum per-order commission.

    Inputs must be nominal-price candidates with no splits. Dividends become
    non-spendable receivables on the event date because payment dates are absent.
    """
    if prices.attrs.get('price_basis') == ADJUSTED_BASIS:
        raise DifferencingError('Adjusted research prices cannot be used for share execution')
    prices = validate_prices(prices)
    if (start > end or not isfinite(initial_capital) or initial_capital <= 0
            or not isfinite(exposure) or not 0 < exposure <= 1
            or not isfinite(buy_cost) or not isfinite(sell_cost)
            or not 0 <= buy_cost <= sell_cost < 1
            or not isfinite(commission_rate) or not 0 <= commission_rate < 1
            or not isfinite(minimum_commission) or minimum_commission < 0):
        raise DifferencingError('Invalid nominal-share simulation settings')
    if (not isfinite(transfer_fee_rate) or not 0 <= transfer_fee_rate < 1
            or not isfinite(stamp_duty_rate) or not 0 <= stamp_duty_rate < 1):
        raise DifferencingError('Invalid transfer fee or stamp duty rate')
    if not isfinite(signal_threshold) or not 0 < signal_threshold < 1:
        raise DifferencingError('Invalid signal threshold')
    if not {'dividends', 'splits'} <= set(prices.columns):
        raise DifferencingError('Nominal-share sensitivity requires explicit action data')
    actions = prices[['dividends', 'splits']].to_numpy(dtype=float)
    if not np.isfinite(actions).all() or (actions < 0).any() or (prices['splits'] != 0).any():
        raise DifferencingError('Missing/invalid actions or splits in nominal-share sample')
    nominal = prices[['open', 'high', 'low', 'close']].to_numpy(dtype=float)
    if (np.abs(nominal * 100 - np.round(nominal * 100)) > 0.002).any():
        raise DifferencingError('Non-cent price data cannot be treated as nominal shares')
    for column in ('open', 'high', 'low', 'close'):
        prices[column] = prices[column].round(2)
    prices = prices[(prices['date'] >= start) & (prices['date'] <= end)]
    daily = {
        date.fromisoformat(str(day)): rows.set_index('instrument').to_dict('index')
        for day, rows in prices.groupby('date')
    }
    days = sorted(daily)
    if len(days) < 2:
        raise DifferencingError('At least two trading days are required')
    symbols = universe.selected
    if any(set(rows) != set(symbols) for rows in daily.values()):
        raise DifferencingError('Missing or unexpected nominal-share market data')
    cash = money(initial_capital)
    receivables = 0.0
    shares: dict[str, int] = {}
    pending = None
    curve, trades = [], []
    total_fees = 0.0
    total_commission = 0.0
    total_transfer_fee = 0.0
    total_stamp_duty = 0.0
    for day in days:
        rows = daily[day]
        # Only shares carried from a previous trading date may be sold today.
        settled = dict(shares)
        receivables = money(receivables + sum(
            quantity * rows[symbol]['dividends'] for symbol, quantity in settled.items()
        ))
        if pending is not None:
            origin, targets = pending
            equity_open = cash + receivables + sum(
                quantity * rows[symbol]['open'] for symbol, quantity in shares.items()
            )
            for symbol in sorted(shares):
                if rows[symbol]['volume'] <= 0:
                    continue
                price = rows[symbol]['open']
                weight = targets.get(symbol, 0.0)
                target_shares = floor(weight * equity_open / price / 100) * 100
                quantity = min(settled.get(symbol, 0), max(0, shares[symbol] - target_shares))
                if target_shares:
                    quantity = quantity // 100 * 100
                if quantity <= 0:
                    continue
                value = money(quantity * price)
                fee_components = execution_fee(
                    value, commission_rate, minimum_commission,
                    transfer_fee_rate, stamp_duty_rate,
                )
                if value <= fee_components['total']:
                    continue
                shares[symbol] -= quantity
                cash = money(cash + value - fee_components['total'])
                total_fees = money(total_fees + fee_components['total'])
                total_commission = money(total_commission + fee_components['commission'])
                total_transfer_fee = money(total_transfer_fee + fee_components['transfer_fee'])
                total_stamp_duty = money(total_stamp_duty + fee_components['stamp_duty'])
                trades.append({
                    'date': day.isoformat(), 'signal_date': origin.isoformat(),
                    'instrument': symbol, 'side': 'SELL', 'quantity': quantity,
                    'price': price, 'value': value, 'cost': fee_components['total'],
                    **fee_components,
                    'sellable_before': settled.get(symbol, 0),
                })
            shares = {symbol: quantity for symbol, quantity in shares.items() if quantity}
            for symbol, weight in sorted(targets.items()):
                if rows[symbol]['volume'] <= 0:
                    continue
                price = rows[symbol]['open']
                target_shares = floor(weight * equity_open / price / 100) * 100
                quantity = max(0, target_shares - shares.get(symbol, 0)) // 100 * 100
                affordable = floor(max(0.0, cash) / (price * (1 + buy_cost)) / 100) * 100
                quantity = min(quantity, affordable)
                while quantity > 0:
                    value = money(quantity * price)
                    fee_components = execution_fee(
                        value, commission_rate, minimum_commission, transfer_fee_rate,
                    )
                    if value + fee_components['total'] <= cash:
                        break
                    quantity -= 100
                if quantity <= 0:
                    continue
                shares[symbol] = shares.get(symbol, 0) + quantity
                cash = money(cash - value - fee_components['total'])
                total_fees = money(total_fees + fee_components['total'])
                total_commission = money(total_commission + fee_components['commission'])
                total_transfer_fee = money(total_transfer_fee + fee_components['transfer_fee'])
                trades.append({
                    'date': day.isoformat(), 'signal_date': origin.isoformat(),
                    'instrument': symbol, 'side': 'BUY', 'quantity': quantity,
                    'price': price, 'value': value, 'cost': fee_components['total'],
                    **fee_components,
                })
        equity = cash + receivables + sum(
            quantity * rows[symbol]['close'] for symbol, quantity in shares.items()
        )
        curve.append({
            'date': day.isoformat(), 'equity': money(equity), 'cash': cash,
            'dividend_receivables': receivables,
        })
        targets = {}
        for symbol in symbols:
            if benchmark:
                active = True
            elif day == days[-1]:
                active = symbol in shares
            elif (day, symbol) not in predictions:
                raise DifferencingError(f'Missing replay forecast for {symbol} on {day}')
            else:
                active = long_only_signal(
                    predictions[(day, symbol)], symbol in shares, signal_threshold,
                )
            if active:
                targets[symbol] = exposure / len(symbols)
        pending = (day, targets)
    equity = np.asarray([initial_capital] + [point['equity'] for point in curve])
    returns = equity[1:] / equity[:-1] - 1
    volatility = float(np.std(returns) * np.sqrt(252))
    return {
        'execution_price_basis': VENDOR_OHLC_BASIS,
        'nominal_prices_verified': False,
        'live_trading_eligible': False,
        'simulation': '有限原价股数规则敏感性测试，非实盘复现',
        'total_return': float(equity[-1] / initial_capital - 1),
        'annualized_return': float((equity[-1] / initial_capital) ** (252 / len(days)) - 1),
        'max_drawdown': float(np.min(equity / np.maximum.accumulate(equity) - 1)),
        'annualized_volatility': volatility,
        'sharpe_zero_risk_free': float(np.mean(returns) * 252 / volatility) if volatility else None,
        'costs': total_fees, 'commission_costs': total_commission,
        'transfer_fees': total_transfer_fee, 'stamp_duty': total_stamp_duty,
        'order_count': len(trades),
        'missing_forecasts': 0, 'equity_curve': curve, 'trades': trades,
        'terminal_shares': shares, 'dividend_receivables': receivables,
        'limitations': [
            '仅使用价格精度检查通过且无拆股的子样本，原价和公司行动未获外部验证。',
            '买入100股整手，卖出不超过前一交易日持仓；本策略仅每日开盘调仓，T+1通常不构成额外限制。',
            '佣金假设为成交额万三、单笔最低5元，含经手费和证管费；券商实际佣金以账户协议为准。',
            '另计沪市过户费万分之0.1双向及卖出印花税千分之0.5。',
            '当前费率统一应用于整个历史测试期，不代表各历史时期实际费率。',
            '缺少分红到账日：除息日计入税前应收资产，全程不作为可用买入现金。',
            '历史ST、涨跌停、股改、配股和公司行动完整性未验证；不模拟冲击成本和盘口成交量。',
            '期末持仓及未到账分红计入资产，不做强制清仓。',
        ],
    }
