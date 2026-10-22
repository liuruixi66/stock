import math

from django.test import SimpleTestCase

from research.fractional_forecast import DifferencingError
from research.fractional_lstm import evaluate_return_predictions


class ReturnPredictionMetricsTests(SimpleTestCase):
    def test_reports_regression_and_direction_metrics(self):
        metrics = evaluate_return_predictions(
            [0.1, -0.1, 0.0],
            [0.2, -0.05, 0.0],
        )

        self.assertEqual(metrics['sample_count'], 3)
        self.assertAlmostEqual(metrics['mae'], 0.05)
        self.assertAlmostEqual(metrics['rmse'], math.sqrt(0.0125 / 3))
        self.assertAlmostEqual(metrics['mape_percent'], 75.0)
        self.assertEqual(metrics['mape_sample_count'], 2)
        self.assertAlmostEqual(metrics['smape_percent'], 400 / 9)
        self.assertEqual(metrics['directional_accuracy_percent'], 100.0)
        self.assertEqual(metrics['zero_actual_return_count'], 1)

    def test_mape_is_unavailable_when_all_actual_returns_are_zero(self):
        metrics = evaluate_return_predictions([0.0, 0.0], [0.0, 0.01])

        self.assertIsNone(metrics['mape_percent'])
        self.assertEqual(metrics['mape_sample_count'], 0)
        self.assertEqual(metrics['zero_actual_return_count'], 2)

    def test_rejects_empty_or_non_finite_values(self):
        for actual, predicted in (
            ([], []),
            ([0.1], []),
            ([float('nan')], [0.1]),
        ):
            with self.subTest(actual=actual, predicted=predicted):
                with self.assertRaises(DifferencingError):
                    evaluate_return_predictions(actual, predicted)
