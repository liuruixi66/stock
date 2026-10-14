from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from strategies import etf_rotation


class Command(BaseCommand):
    help = 'Export a standalone BigQuant AIStudio ETF backtest/paper strategy.'
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument('--output', type=Path, required=True)

    def handle(self, *args, **options):
        root = Path(etf_rotation.__file__).parent
        core = (root / 'etf_rotation.py').read_text(encoding='utf-8')
        adapter = (root / 'platforms' / 'bigquant_etf_rotation.py').read_text(encoding='utf-8')
        local_import = 'from strategies.etf_rotation import RotationBar, RotationConfig, build_rotation_targets\n'
        if adapter.count(local_import) != 1:
            raise CommandError('Adapter core import changed; export needs updating')
        output = options['output']
        if output.exists():
            raise CommandError('Refusing to overwrite existing file: {}'.format(output))
        try:
            output.write_text(core + '\n\n' + adapter.replace(local_import, ''), encoding='utf-8')
        except OSError as exc:
            raise CommandError('Could not write strategy: {}'.format(exc)) from exc
        self.stdout.write(self.style.SUCCESS('Standalone BigQuant strategy: {}'.format(output)))
