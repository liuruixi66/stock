import ast
import json
from datetime import date
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from market_data import HistoricalBar
from market_data.local_history import download_history
from strategies.etf_rotation import build_rotation_targets
from stockmarket.tests.test_etf_rotation import trending_history


class ETFCommandTests(SimpleTestCase):
    def test_export_writes_single_file_and_refuses_overwrite(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / 'strategy.py'
            call_command('export_joinquant_etf', '--output', str(output), stdout=StringIO())
            content = output.read_text(encoding='utf-8')
            ast.parse(content, feature_version=(3, 8))
            self.assertNotIn('from stockmarket', content)
            self.assertIn('def initialize(context)', content)
            self.assertIn('def build_rotation_targets(', content)
            with self.assertRaisesRegex(CommandError, 'overwrite'):
                call_command('export_joinquant_etf', '--output', str(output))
            self.assertEqual(output.read_text(encoding='utf-8'), content)

    def test_export_write_error_is_explicit(self):
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(CommandError, 'Could not write'):
                call_command('export_joinquant_etf', '--output',
                             str(Path(directory) / 'missing' / 'strategy.py'))

    def test_missing_snapshot_is_error_not_network_fallback(self):
        with TemporaryDirectory() as directory, patch(
                'market_data.local_history.get_provider') as network:
            with self.assertRaisesRegex(CommandError, 'Local history missing'):
                call_command(
                    'etf_rotation_signals', '--symbols', '510300',
                    '--start', '2024-01-01', '--as-of', '2024-06-01',
                    '--data-dir', directory,
                )
            network.assert_not_called()

    def test_invalid_date_and_symbols_are_errors(self):
        with self.assertRaisesRegex(CommandError, 'Require start'):
            call_command('etf_rotation_signals', '--symbols', '510300',
                         '--start', '2024-01-01', '--as-of', date.today().isoformat())
        for symbols in (['510300.XSHG'], ['510300', '510300']):
            with self.subTest(symbols=symbols), self.assertRaisesRegex(
                    CommandError, 'unique six-digit'):
                call_command('etf_rotation_signals', '--symbols', *symbols,
                             '--start', '2024-01-01', '--as-of', '2024-06-01')

    @patch('market_data.local_history.get_provider')
    def test_offline_signal_uses_exact_core_and_includes_provenance(self, network):
        bars = trending_history()
        start, end = bars[0].date, bars[-1].date
        network.return_value.get_history.return_value = [
            HistoricalBar(bar.date, bar.close, bar.high, bar.low, bar.close, int(bar.volume))
            for bar in bars
        ]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            download_history('A', '510300', start, end, root)
            network.reset_mock()
            output = StringIO()
            call_command(
                'etf_rotation_signals', '--symbols', '510300',
                '--start', start.isoformat(), '--as-of', end.isoformat(),
                '--data-dir', directory, stdout=output,
            )
            result = json.loads(output.getvalue())
            expected = build_rotation_targets({'510300': bars}, end)
            self.assertEqual(result['weights'], expected['weights'])
            self.assertEqual(result['as_of'], end.isoformat())
            self.assertIn('sha256', result['datasets']['510300'])
            self.assertIn('not_applied_offline', result['execution_filters'])
            network.assert_not_called()
