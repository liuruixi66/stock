from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from market_data import MarketDataError
from market_data.local_history import RESEARCH_START, RESEARCH_UNIVERSE, available_end, download_history


class Command(BaseCommand):
    help = 'Download frozen daily research history; existing snapshots are never overwritten.'

    def add_arguments(self, parser):
        parser.add_argument('--market', choices=['ALL', *RESEARCH_UNIVERSE], default='ALL')
        parser.add_argument('--symbols', nargs='+')
        parser.add_argument('--start', type=date.fromisoformat, default=RESEARCH_START)
        parser.add_argument('--end', type=date.fromisoformat, default=available_end())
        parser.add_argument('--output', type=Path)

    def handle(self, *args, **options):
        start = options['start']
        requested_end = options['end']
        end = min(requested_end, datetime.now(timezone.utc).date() - timedelta(days=1))
        if start > end:
            raise CommandError('Start must not exceed the last completed UTC day')
        if options['symbols'] and options['market'] == 'ALL':
            raise CommandError('--symbols requires a single --market')
        if end != requested_end:
            self.stdout.write(self.style.WARNING(f'End capped from {requested_end} to {end}; future/incomplete days excluded.'))
        self.stdout.write(f'History range: {start}..{end}; interval=1d')
        markets = RESEARCH_UNIVERSE if options['market'] == 'ALL' else [options['market']]
        failures = []
        completed = 0
        for market in markets:
            for symbol in options['symbols'] or RESEARCH_UNIVERSE[market]:
                self.stdout.write(f'Downloading {market}/{symbol}...')
                self.stdout.flush()
                try:
                    metadata = download_history(market, symbol, start, end, options['output'])
                except (MarketDataError, OSError) as exc:
                    failures.append(f'{market}/{symbol}: {exc}')
                    self.stderr.write(self.style.ERROR(failures[-1]))
                    continue
                completed += 1
                action = 'CACHED' if metadata['cached'] else 'SAVED'
                self.stdout.write(f"{action} {market}/{symbol}: {metadata['bar_count']} bars, {metadata['first_bar']}..{metadata['last_bar']}, sha256={metadata['sha256']}")
        self.stdout.write(f'Completed: {completed}; failed: {len(failures)}')
        if failures:
            raise CommandError('Some datasets were not downloaded. Successful snapshots are retained; rerun to retry failures.')