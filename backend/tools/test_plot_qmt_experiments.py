import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from tools.plot_qmt_experiments import (
    load_operations, load_experiments, render, yearly_operation_profit,
    load_nav, yearly_nav_returns,
)


class QmtPlotTests(unittest.TestCase):
    def test_existing_exports_and_missing_report_metrics(self):
        root = Path(__file__).resolve().parents[2]
        experiments, output = load_experiments(root / 'qmt_experiments.json')
        self.assertEqual([len(e['rows']) for e in experiments], [260, 461, 473, 584])
        self.assertAlmostEqual(experiments[0]['fees'], 7285.117, places=3)
        self.assertAlmostEqual(experiments[1]['fees'], 18237.144, places=3)
        self.assertEqual(experiments[1]['metrics'], {})
        self.assertEqual(output.suffix, '.png')
        self.assertIsNotNone(experiments[3]['rows'][0]['date'])
        self.assertEqual(experiments[3]['rows'][0]['side'], '买入')
        self.assertAlmostEqual(experiments[3]['profit'], -42190.305, places=3)

    def test_summary_export_does_not_invent_dates_or_trade_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'summary.txt'
            path.write_text(
                '代码\t累计盈亏\t累计交易费用\n510300\t-100\t5\n',
                encoding='utf-8',
            )
            rows = load_operations(path)
            self.assertEqual(len(rows), 1)
            self.assertIsNone(rows[0]['date'])
            self.assertIsNone(rows[0]['side'])
            self.assertEqual(rows[0]['profit'], -100)

    def test_png_render(self):
        root = Path(__file__).resolve().parents[2]
        experiments, _ = load_experiments(root / 'qmt_experiments.json')
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'comparison.png'
            render(experiments, output)
            self.assertEqual(output.read_bytes()[:8], b'\x89PNG\r\n\x1a\n')
            self.assertGreater(output.stat().st_size, 10000)

    def test_bad_amount_fails_explicitly(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'export.txt'
            output.write_text(
                '代码\t操作时间\t操作类型\t盈利\t交易费用\n'
                '510300\t2025-01-01 15:00:00\t买入\tNaN\t5\n',
                encoding='utf-8',
            )
            with self.assertRaisesRegex(ValueError, 'Invalid operation amount'):
                load_operations(output)

    def test_yearly_profit_sums_buys_and_sells_without_double_deducting_fees(self):
        rows = [
            {'date': datetime(2024, 1, 1), 'profit': -5.0, 'fee': 5.0},
            {'date': datetime(2024, 12, 31), 'profit': 105.0, 'fee': 5.0},
            {'date': datetime(2025, 1, 1), 'profit': -30.0, 'fee': 5.0},
        ]
        self.assertEqual(yearly_operation_profit(rows), {2024: 100.0, 2025: -30.0})
        self.assertEqual(yearly_operation_profit([{'date': None, 'profit': 100}]), {})

    def test_yearly_totals_reconcile_with_each_export(self):
        root = Path(__file__).resolve().parents[2]
        experiments, _ = load_experiments(root / 'qmt_experiments.json')
        for experiment in experiments:
            totals = yearly_operation_profit(experiment['rows'])
            self.assertEqual(list(totals), sorted(totals))
            self.assertAlmostEqual(sum(totals.values()), experiment['profit'], places=6)

    def test_nav_annual_returns_include_market_value_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'nav.csv'
            path.write_text(
                'date,nav\n2024-01-01,100\n2024-12-31,110\n2025-11-01,99\n',
                encoding='utf-8',
            )
            totals = yearly_nav_returns(load_nav(path))
            self.assertAlmostEqual(totals[2024], 0.10)
            self.assertAlmostEqual(totals[2025], -0.10)

    def test_invalid_nav_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'nav.csv'
            for text in (
                    'date,nav\n2024-01-01,100\n2024-01-01,110\n',
                    'date,nav\n2024-01-01,100\n2024-01-02,NaN\n'):
                path.write_text(text, encoding='utf-8')
                with self.assertRaises(ValueError):
                    load_nav(path)


if __name__ == '__main__':
    unittest.main()
