"""Explicit price semantics shared by database research and sensitivity tools."""

import hashlib
import math


PRICE_POLICY_VERSION = 'fractional-price-policy-v1'
ADJUSTED_BASIS = 'vendor_adjusted_ohlc_snapshot'
VENDOR_OHLC_BASIS = 'vendor_ohlc_nominal_unverified'


def research_price_contract() -> dict:
    """Return a fresh contract; this is not a certificate for live execution."""
    return {
        'version': PRICE_POLICY_VERSION,
        'model_input_basis': ADJUSTED_BASIS,
        'adjustment_formula': 'OHLC * adj_close / close; volume unchanged',
        'adjustment_anchor': 'vendor_snapshot_not_certified_qfq_or_hfq',
        'prediction_target': 'next_session_adjusted_close_simple_return',
        'signal_timing': 'after_close_t_for_open_t_plus_1',
        'selection_protocol': 'per_stock_daily_pre_target_validation_mse',
        'research_execution': 'adjusted_prices_fractional_units_no_cash_dividends',
        'share_execution_requires': 'verified_nominal_OHLC_and_corporate_actions',
        'point_in_time_verified': False,
        'nominal_prices_verified': False,
        'live_trading_eligible': False,
    }


def adjusted_ohlc(open_price, high, low, close, adjusted_close) -> tuple[float, ...]:
    """Never substitute an unadjusted close when adjustment data is missing."""
    try:
        values = tuple(float(v) for v in (open_price, high, low, close, adjusted_close))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError('Missing or invalid adjusted OHLC price') from exc
    if any(not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError('Adjusted OHLC prices must be finite and positive')
    open_value, high_value, low_value, close_value, adjusted_value = values
    if low_value > min(open_value, close_value) or high_value < max(open_value, close_value):
        raise ValueError('Invalid OHLC price ordering')
    factor = adjusted_value / close_value
    result = tuple(v * factor for v in values[:4])
    if any(not math.isfinite(v) or v <= 0 for v in result):
        raise ValueError('Adjusted OHLC overflow or underflow')
    return result


def frame_digest(frame, columns) -> str:
    ordered = frame.sort_values(['instrument', 'date'])[list(columns)]
    return hashlib.sha256(
        ordered.to_csv(index=False, float_format='%.12g', lineterminator='\n').encode('utf-8'),
    ).hexdigest()


PRICE_COLUMNS = ('date', 'instrument', 'open', 'high', 'low', 'close', 'volume')
ACTION_COLUMNS = ('date', 'instrument', 'dividends', 'splits')
