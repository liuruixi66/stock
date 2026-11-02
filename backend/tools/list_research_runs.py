"""List numbered runs without mistaking unfinished training for latest results."""

import argparse
import json
from pathlib import Path

from research.experiment_runs import DEFAULT_RUN_ROOT, KINDS, latest_completed, read_runs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument('--kind', choices=KINDS)
    parser.add_argument('--latest', action='store_true', help='Only latest successful result')
    args = parser.parse_args()
    try:
        if args.latest:
            record = latest_completed(args.root, args.kind)
            print(json.dumps(record, ensure_ascii=False, indent=2) if record
                  else 'No successfully completed numbered run yet.')
        else:
            for record in read_runs(args.root):
                if args.kind is None or record['kind'] == args.kind:
                    print(f'{record["run_id"]}  {record["status"]:12}  '
                          f'{str(record["kind"]):20}  {record["artifact"]}')
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f'Run listing failed: {exc}\n')


if __name__ == '__main__':
    main()
