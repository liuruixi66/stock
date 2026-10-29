"""Sequential experiment identities; latest means successfully completed."""

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import re
import time
from uuid import uuid4


DEFAULT_RUN_ROOT = Path(__file__).resolve().parents[1] / 'research_charts' / 'runs'
KINDS = ('fractional-training', 'fractional-search', 'rotation-training')


def timestamp():
    return datetime.now().astimezone().isoformat()


def read_runs(root=DEFAULT_RUN_ROOT):
    records = []
    for directory in Path(root).glob('run-*'):
        match = re.fullmatch(r'run-(\d{6,})', directory.name)
        if not directory.is_dir() or not match:
            continue
        path = directory / 'run.json'
        if not path.exists():
            records.append({'run_id': directory.name, 'number': int(match[1]),
                            'status': 'initializing', 'kind': None, 'artifact': None})
            continue
        record = json.loads(path.read_text(encoding='utf-8'))
        if record['run_id'] != directory.name or record['number'] != int(match[1]):
            raise ValueError(f'Run identity mismatch: {path}')
        records.append(record)
    return sorted(records, key=lambda row: row['number'])


def latest_completed(root=DEFAULT_RUN_ROOT, kind=None):
    return next((row for row in reversed(read_runs(root))
                 if row['status'] == 'completed' and (kind is None or row['kind'] == kind)), None)


@dataclass
class ExperimentRun:
    directory: Path
    metadata: dict

    @property
    def artifact(self):
        return Path(self.metadata['artifact'])

    @property
    def run_id(self):
        return self.metadata['run_id']

    def save(self):
        temporary = self.directory / f'.run-{uuid4().hex}.tmp'
        try:
            with temporary.open('x', encoding='utf-8') as stream:
                json.dump(self.metadata, stream, ensure_ascii=False, allow_nan=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            for attempt in range(5):
                try:
                    os.replace(temporary, self.directory / 'run.json')
                    break
                except PermissionError:
                    if attempt == 4:
                        raise
                    time.sleep(.02 * (attempt + 1))
        finally:
            temporary.unlink(missing_ok=True)


@contextmanager
def tracked_run(kind, artifact=None, *, resume=False, root=DEFAULT_RUN_ROOT):
    if kind not in KINDS:
        raise ValueError(f'Unknown experiment kind: {kind}')
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    artifact = Path(artifact).resolve() if artifact is not None else None
    records = read_runs(root)
    previous = next((row for row in reversed(records)
                     if row['kind'] == kind and artifact is not None
                     and row['artifact'] == str(artifact)), None)
    if previous:
        if not resume or previous['status'] == 'completed':
            raise ValueError('Output is already registered; resume an unfinished run or use a new output')
        record = ExperimentRun(root / previous['run_id'], previous)
        record.metadata['attempts'] += 1
        record.metadata.pop('error', None)
        record.metadata.pop('finished_at', None)
    else:
        number = max((row['number'] for row in records), default=0) + 1
        while True:
            directory = root / f'run-{number:06d}'
            try:
                directory.mkdir()
                break
            except FileExistsError:
                number += 1
        if artifact is None:
            artifact = (
                directory / 'search' / 'report.json' if kind == 'fractional-search'
                else directory / 'artifacts' / 'results.json' if kind == 'rotation-training'
                else directory / 'results.json'
            )
        record = ExperimentRun(directory, {
            'run_id': directory.name, 'number': number, 'kind': kind,
            'artifact': str(artifact), 'created_at': timestamp(), 'attempts': 1,
        })
    record.metadata.update(status='running', started_at=timestamp(), pid=os.getpid())
    record.save()
    try:
        yield record
        if not record.artifact.is_file():
            raise ValueError(f'Run did not produce its result artifact: {record.artifact}')
    except BaseException as exc:
        record.metadata.update(
            status='interrupted' if isinstance(exc, KeyboardInterrupt) else 'failed',
            finished_at=timestamp(), error=f'{type(exc).__name__}: {exc}',
        )
        record.save()
        raise
    else:
        record.metadata.update(status='completed', finished_at=timestamp())
        record.save()
