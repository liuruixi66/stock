import ast
from pathlib import Path
import unittest

from strategies.qmt_fractional_probe import diagnostic_weights, run_probe


class QmtFractionalProbeTests(unittest.TestCase):
    def test_weights_match_research(self):
        from research.fractional_forecast import fractional_weights

        for order in (0.0, 0.25, 0.5, 0.75, 1.0):
            self.assertEqual(diagnostic_weights(order), fractional_weights(order).tolist())

    def test_invalid_weights_fail(self):
        for order in (-0.1, 1.1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                diagnostic_weights(order)
        with self.assertRaises(ValueError):
            diagnostic_weights(max_lags=2)

    def test_cpu_training_and_inference(self):
        result = run_probe('cpu')
        self.assertEqual(result['device'], 'cpu')
        self.assertGreater(result['training_samples'], 0)
        self.assertGreater(result['validation_samples'], 0)

    def test_only_explicit_non_io_imports(self):
        path = Path(__file__).with_name('qmt_fractional_probe.py')
        tree = ast.parse(path.read_text(encoding='ascii'))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            self.assertNotIsInstance(node, ast.ImportFrom)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, (
                    'open', 'eval', 'exec', 'compile', '__import__',
                    'passorder', 'order_shares', 'get_trade_detail_data',
                ))
        self.assertEqual(set(imports), {'math', 'sys', 'torch'})


if __name__ == '__main__':
    unittest.main()
