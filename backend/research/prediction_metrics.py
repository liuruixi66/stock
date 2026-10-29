"""Return prediction metrics independent of market-data provider imports."""

from typing import Sequence

import numpy as np


def evaluate_return_predictions(
    actual_returns: Sequence[float], predicted_returns: Sequence[float],
) -> dict:
    actual = np.asarray(actual_returns, dtype=float)
    predicted = np.asarray(predicted_returns, dtype=float)
    if (actual.ndim != 1 or predicted.ndim != 1 or len(actual) == 0
            or len(actual) != len(predicted)
            or not np.isfinite(actual).all() or not np.isfinite(predicted).all()):
        raise ValueError('Return evaluation requires equally sized, nonempty finite vectors')
    with np.errstate(over='ignore', divide='ignore', invalid='ignore'):
        errors = predicted - actual
        nonzero_actual = actual != 0
        absolute_errors = np.abs(errors)
        percentage_denominator = np.abs(actual) + np.abs(predicted)
        smape_terms = np.divide(
            2 * absolute_errors, percentage_denominator,
            out=np.zeros_like(absolute_errors), where=percentage_denominator > 0,
        )
        metrics = {
            'sample_count': int(len(actual)),
            'mae': float(np.mean(absolute_errors)),
            'rmse': float(np.sqrt(np.mean(np.square(errors)))),
            'mape_percent': (
                float(np.mean(absolute_errors[nonzero_actual] / np.abs(actual[nonzero_actual])) * 100)
                if nonzero_actual.any() else None
            ),
            'mape_sample_count': int(nonzero_actual.sum()),
            'smape_percent': float(np.mean(smape_terms) * 100),
            'directional_accuracy_percent': float(
                np.mean(np.sign(actual) == np.sign(predicted)) * 100
            ),
            'zero_actual_return_count': int((~nonzero_actual).sum()),
        }
    if any(value is not None and isinstance(value, float) and not np.isfinite(value)
           for value in metrics.values()):
        raise ValueError('Return evaluation produced non-finite metrics')
    return metrics
