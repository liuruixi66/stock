import ast
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase
from django.urls import resolve, reverse

from api.cache_views import get_cache_dir
from config.paths import BASE_DIR, CACHE_DIR


class BackendStructureTests(SimpleTestCase):
    def test_paths_and_django_app_identity_are_preserved(self):
        self.assertEqual(BASE_DIR, Path(__file__).resolve().parents[2])
        self.assertEqual(CACHE_DIR, BASE_DIR / 'cache')
        self.assertEqual(Path(get_cache_dir()), CACHE_DIR)
        self.assertEqual(settings.ROOT_URLCONF, 'config.urls')
        self.assertEqual(settings.WSGI_APPLICATION, 'config.wsgi.application')
        self.assertIn('stockmarket', settings.INSTALLED_APPS)
        self.assertTrue((BASE_DIR / 'stockmarket' / 'migrations').is_dir())

    def test_existing_routes_keep_their_paths_and_names(self):
        routes = {
            'market_quotes': '/api/market/quotes/',
            'market_history': '/api/market/history/',
            'market_minute_data': '/api/market/minute/',
            'paper_accounts': '/api/paper/accounts/',
            'paper_brokers': '/api/paper/brokers/',
            'paper_orders': '/api/paper/orders/',
            'research_backtest': '/api/research/backtest/',
            'portfolio_backtest': '/api/research/portfolio-backtest/',
            'leaky_forecast_experiment': '/api/research/leaky-forecast/',
            'research_runs': '/api/research/runs/',
            'watchlist': '/api/watchlist/',
            'cache_backtest_details': '/api/cache/backtest-details/',
            'cache_status': '/api/cache/status/',
        }
        parameterized = {
            'paper_order_cancel': ('order_id', '/api/paper/orders/7/cancel/'),
            'paper_account_summary': ('account_id', '/api/paper/accounts/7/summary/'),
            'paper_account_sync': ('account_id', '/api/paper/accounts/7/sync/'),
            'paper_account_analytics': ('account_id', '/api/paper/accounts/7/analytics/'),
            'research_run_detail': ('run_id', '/api/research/runs/7/'),
            'watchlist_item': ('item_id', '/api/watchlist/7/'),
        }
        for name, path in routes.items():
            with self.subTest(name=name):
                self.assertEqual(reverse(name), path)
                self.assertEqual(resolve(path).url_name, name)
        for name, (argument, path) in parameterized.items():
            with self.subTest(name=name):
                self.assertEqual(reverse(name, kwargs={argument: 7}), path)
                self.assertEqual(resolve(path).url_name, name)

    def test_rule_modules_do_not_depend_on_web_or_execution_layers(self):
        forbidden = {'django', 'stockmarket', 'api', 'config', 'execution', 'brokers'}
        for path in (BASE_DIR / 'strategies').glob('*.py'):
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    modules = [node.module or '']
                else:
                    continue
                with self.subTest(path=path.name, line=node.lineno):
                    self.assertFalse(forbidden & {module.split('.')[0] for module in modules})

    def test_core_import_does_not_initialize_django(self):
        env = dict(os.environ)
        env.pop('DJANGO_SETTINGS_MODULE', None)
        result = subprocess.run(
            [sys.executable, '-c',
             "import sys; import strategies.etf_rotation; assert 'django' not in sys.modules"],
            cwd=BASE_DIR, env=env, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_bigquant_export_is_unchanged_by_module_relocation(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / 'bigquant.py'
            call_command('export_bigquant_etf', '--output', str(output))
            self.assertEqual(
                output.read_text(encoding='utf-8'),
                (BASE_DIR.parent / 'bigquant_etf_rotation_v1.py').read_text(encoding='utf-8'),
            )

    def test_screening_service_has_no_web_or_django_bootstrap(self):
        tree = ast.parse((BASE_DIR / 'research' / 'screening.py').read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertNotEqual(node.module, 'django.http')
            elif isinstance(node, ast.FunctionDef):
                self.assertFalse(node.name.endswith('_api'))
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                self.assertNotIn(ast.unparse(node.func), {'django.setup', 'os.chdir'})
