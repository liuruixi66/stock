from concurrent.futures import ThreadPoolExecutor
from functools import partial
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from research.experiment_runs import latest_completed, read_runs, tracked_run


class ExperimentRunTests(TestCase):
    def test_numbers_are_monotonic_and_failures_are_not_latest_success(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with tracked_run('fractional-training', root=root) as run:
                self.assertEqual(run.run_id, 'run-000001')
                self.assertEqual(read_runs(root)[0]['status'], 'running')
                run.artifact.write_text('{}')
            with self.assertRaisesRegex(RuntimeError, 'training failed'):
                with tracked_run('fractional-training', root=root):
                    raise RuntimeError('training failed')
            self.assertEqual(latest_completed(root)['run_id'], 'run-000001')
            self.assertEqual(read_runs(root)[1]['status'], 'failed')
            with tracked_run('fractional-search', root=root) as run:
                run.artifact.parent.mkdir()
                run.artifact.write_text('{}')
            self.assertEqual(latest_completed(root)['run_id'], 'run-000003')
            self.assertEqual(latest_completed(root, 'fractional-training')['run_id'], 'run-000001')

    def test_resume_reuses_identity_and_cannot_relabel_completed_run(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / 'explicit.json'
            with self.assertRaises(KeyboardInterrupt):
                with tracked_run('fractional-training', artifact, root=root):
                    raise KeyboardInterrupt()
            self.assertEqual(read_runs(root)[0]['status'], 'interrupted')
            with tracked_run('fractional-training', artifact, resume=True, root=root) as run:
                self.assertEqual(run.run_id, 'run-000001')
                run.artifact.write_text('{}')
            self.assertEqual(len(read_runs(root)), 1)
            self.assertEqual(read_runs(root)[0]['attempts'], 2)
            self.assertNotIn('error', read_runs(root)[0])
            with self.assertRaises(ValueError):
                with tracked_run('fractional-training', artifact, resume=True, root=root):
                    pass

    def test_missing_result_is_failed_and_empty_registry_has_no_latest(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertIsNone(latest_completed(root))
            with self.assertRaisesRegex(ValueError, 'did not produce'):
                with tracked_run('fractional-training', root=root):
                    pass
            self.assertEqual(read_runs(root)[0]['status'], 'failed')
            self.assertIsNone(latest_completed(root))

    def test_concurrent_allocations_have_unique_ids(self):
        with TemporaryDirectory() as directory:
            def execute(_):
                with tracked_run('fractional-training', root=Path(directory)) as run:
                    run.artifact.write_text('{}')
                    return run.run_id

            with ThreadPoolExecutor(max_workers=4) as executor:
                ids = list(executor.map(execute, range(12)))
            self.assertEqual(len(set(ids)), 12)
            self.assertEqual(sorted(ids)[-1], 'run-000012')
            self.assertEqual(len(read_runs(Path(directory))), 12)
            self.assertTrue(all(row['status'] == 'completed' for row in read_runs(Path(directory))))

    def test_transient_windows_manifest_lock_is_retried(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            replace = os.replace
            attempts = 0

            def locked_then_replace(source, destination):
                nonlocal attempts
                attempts += 1
                if attempts < 3:
                    raise PermissionError('Reader temporarily holds run.json')
                return replace(source, destination)

            with patch('research.experiment_runs.os.replace', side_effect=locked_then_replace), patch(
                'research.experiment_runs.time.sleep',
            ):
                with tracked_run('fractional-training', root=root) as run:
                    run.artifact.write_text('{}')
            self.assertEqual(latest_completed(root)['run_id'], 'run-000001')
            self.assertEqual(attempts, 4)

    def test_fractional_training_cli_defaults_to_numbered_output(self):
        from tools.run_fractional_research import main

        with TemporaryDirectory() as directory:
            root = Path(directory)

            def execute(args, parser, experiment):
                self.assertEqual(args.output, experiment.artifact)
                self.assertEqual(args.log_directory, experiment.directory / 'logs')
                args.output.write_text('{}')

            with patch('sys.argv', ['train']), patch(
                'tools.run_fractional_research.tracked_run', partial(tracked_run, root=root),
            ), patch('tools.run_fractional_research._execute', side_effect=execute):
                main()
            self.assertEqual(latest_completed(root)['kind'], 'fractional-training')

    def test_search_and_rotation_cli_use_the_same_registry(self):
        from tools.run_market_rotation import main as rotation_main
        from tools.tune_fractional_lstm import main as search_main

        with TemporaryDirectory() as directory:
            root = Path(directory)

            def search(database, destination, settings, **options):
                destination.mkdir()
                report = {'parameters': {}, 'data_provenance': {}, 'methods': {}}
                (destination / 'report.json').write_text(json.dumps(report))
                return report

            with patch('sys.argv', ['search']), patch(
                'tools.tune_fractional_lstm.tracked_run', partial(tracked_run, root=root),
            ), patch('tools.tune_fractional_lstm.run_search', side_effect=search):
                search_main()
            database = root / 'stocks.db'
            database.touch()

            def execute(args, experiment):
                self.assertEqual(args.output_directory, experiment.artifact.parent)
                args.output_directory.mkdir()
                experiment.artifact.write_text('{}')

            with patch('sys.argv', ['rotation', '--database', str(database)]), patch(
                'research.experiment_runs.tracked_run', partial(tracked_run, root=root),
            ), patch('tools.run_market_rotation._execute', side_effect=execute):
                rotation_main()
            self.assertEqual([row['run_id'] for row in read_runs(root)], ['run-000001', 'run-000002'])
            self.assertEqual(latest_completed(root)['kind'], 'rotation-training')
