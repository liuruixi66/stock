from dataclasses import replace
from datetime import date, timedelta
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from unittest import skipUnless

import numpy as np
import pandas as pd
from django.test import SimpleTestCase

from research.fractional_forecast import DifferencingError, ForecastConfig, invert_one_step
from research.fractional_lstm import (
    EarlyStopping, LSTMTrial, atomic_replace, build_network, fit_trial, load_training_checkpoint,
    prepare_sequences, save_training_checkpoint, train_stock,
)
from research.fractional_results import chinese_result


def small_prices():
    days = [date(2024, 1, 1) + timedelta(days=i) for i in range(95)]
    close = 100 * np.exp(np.cumsum(0.002 * np.sin(np.arange(95)) + 0.0001))
    frame = pd.DataFrame({
        'date': days, 'instrument': '600001.SH', 'open': close,
        'high': close * 1.01, 'low': close * 0.99,
        'close': close, 'volume': 10000,
    })
    config = ForecastConfig(
        train_start=days[0], validation_start=days[65],
        test_start=days[92], test_end=days[94], sequence_length=3,
        minimum_train_samples=20, minimum_validation_samples=5,
    )
    return frame, config


@skipUnless(importlib.util.find_spec('torch'), 'Optional research dependency: torch')
class TrainingControlsTests(SimpleTestCase):
    def test_windows_atomic_replace_retries_only_transient_locks(self):
        locked = PermissionError('sharing violation')
        locked.winerror = 32
        with patch('research.fractional_lstm.os.replace', side_effect=[locked, None]) as replace, patch(
            'research.fractional_lstm.time.sleep',
        ), self.assertLogs('research.fractional_lstm', level='WARNING'):
            atomic_replace(Path('best.pt.tmp'), Path('best.pt'))
        self.assertEqual(replace.call_count, 2)
        with patch('research.fractional_lstm.os.replace', side_effect=PermissionError('denied')):
            with self.assertRaises(PermissionError):
                atomic_replace(Path('best.pt.tmp'), Path('best.pt'))

    def test_trial_rejects_invalid_structure(self):
        for changes in (
            {'num_layers': 0}, {'dropout': 0.1}, {'dropout': float('nan')},
            {'num_layers': 2, 'dropout': 1.0},
        ):
            with self.subTest(changes=changes):
                with self.assertRaises(DifferencingError):
                    replace(LSTMTrial(), **changes).validate()
        LSTMTrial(num_layers=2, dropout=0.1).validate()

    def test_small_improvements_save_best_without_resetting_patience(self):
        stopping = EarlyStopping(patience=2, min_delta=0.1)
        self.assertEqual(stopping.observe(1.0, 1), (True, False))
        self.assertEqual(stopping.observe(0.96, 2), (True, False))
        self.assertEqual(stopping.observe(0.95, 3), (True, True))
        self.assertEqual(stopping.best_epoch, 3)
        self.assertEqual(stopping.best_score, 0.95)
        with self.assertRaises(DifferencingError):
            stopping.observe(float('nan'), 4)

    def test_disabled_stopping_does_not_stop(self):
        stopping = EarlyStopping(patience=0)
        for epoch in range(1, 25):
            _, stop = stopping.observe(float(epoch), epoch)
            self.assertFalse(stop)

    def test_best_checkpoint_round_trip_and_structure(self):
        import torch

        for layers in (1, 2):
            with self.subTest(layers=layers), TemporaryDirectory() as directory:
                trial = LSTMTrial(hidden_size=4, num_layers=layers)
                model = build_network(3, trial)
                payload = {
                    'kind': 'validation_selection', 'trial': trial.__dict__,
                    'feature_count': 3, 'model': model.state_dict(),
                    'scaler': {'y_mean': 0.0, 'y_scale': 1.0},
                }
                path = Path(directory) / 'best.pt'
                save_training_checkpoint(path, payload)
                loaded, restored = load_training_checkpoint(path)
                x = torch.zeros(2, 5, 3)
                model.eval()
                restored.eval()
                torch.testing.assert_close(model(x), restored(x))
                self.assertEqual(loaded['kind'], 'validation_selection')
                self.assertFalse(path.with_suffix('.pt.tmp').exists())

    def test_fit_restores_actual_best_epoch_and_finite_history(self):
        import torch

        torch.set_num_threads(1)
        torch.manual_seed(7)
        x = torch.randn(24, 4, 3)
        y = torch.randn(24)
        trial = LSTMTrial(hidden_size=4, epochs=4, batch_size=8)
        result = fit_trial(
            x, y, torch.arange(16), torch.arange(16, 24), trial, seed=7,
            patience=2, min_delta=1e-6,
        )
        history = result['epoch_history']
        self.assertLessEqual(len(history), 4)
        self.assertEqual(
            result['epoch'],
            min(history, key=lambda row: row['selection_score'])['epoch'],
        )
        self.assertTrue(np.isfinite(result['selection_score']))
        model = build_network(3, trial)
        model.load_state_dict(result['model'])
        model.eval()
        with torch.no_grad():
            mse = torch.mean((model(x[16:]) - y[16:]) ** 2).item()
        self.assertAlmostEqual(mse, result['validation_mse_scaled'], places=6)

    def test_legacy_fit_matches_original_fixed_epoch_loop(self):
        import torch

        torch.set_num_threads(1)
        torch.manual_seed(9)
        x, y = torch.randn(24, 4, 3), torch.randn(24)
        trial = LSTMTrial(hidden_size=4, epochs=3, batch_size=8)
        torch.manual_seed(42)
        model = build_network(3, trial)
        optimizer = torch.optim.Adam(model.parameters(), lr=trial.learning_rate)
        best_loss, best_state = float('inf'), None
        for _ in range(trial.epochs):
            model.train()
            for batch in torch.arange(16).split(trial.batch_size):
                optimizer.zero_grad()
                loss = torch.nn.functional.mse_loss(model(x[batch]), y[batch])
                loss.backward()
                optimizer.step()
            model.eval()
            with torch.no_grad():
                score = torch.nn.functional.mse_loss(model(x[16:]), y[16:]).item()
            if score < best_loss:
                best_loss = score
                best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        result = fit_trial(x, y, torch.arange(16), torch.arange(16, 24), trial)
        self.assertEqual(result['validation_mse_scaled'], best_loss)
        self.assertEqual(len(result['epoch_history']), trial.epochs)
        for key in best_state:
            torch.testing.assert_close(result['model'][key], best_state[key], rtol=0, atol=0)

    def test_invalid_loss_and_overlapping_validation_are_errors(self):
        import torch

        x, y = torch.zeros(8, 3, 2), torch.full((8,), float('nan'))
        for validation in (torch.arange(4, 8), torch.arange(2, 6)):
            with self.assertRaises(DifferencingError):
                fit_trial(x, y, torch.arange(4), validation, LSTMTrial(epochs=1))

    def test_walk_forward_refit_checkpoint_reproduces_forecast(self):
        import torch

        frame, config = small_prices()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            metadata, forecasts = train_stock(
                frame, config, 'log_return',
                [LSTMTrial(hidden_size=4, epochs=2)], walk_forward_validation_days=5,
                patience=1, selection_metric='return_mae', checkpoint_directory=root,
            )
            path = root / '600001.SH-log_return' / 'refit-latest.pt'
            payload, model = load_training_checkpoint(path)
            self.assertEqual(payload['kind'], 'pre_target_refit')
            self.assertTrue(payload['selected_prices_sha256'])
            selection, _ = load_training_checkpoint(path.with_name('validation-best.pt'))
            self.assertEqual(selection['kind'], 'validation_selection')
            data = prepare_sequences(frame, config, 1.0)
            scaler = payload['scaler']
            x = ((data['raw_x'][-1:] - np.asarray(scaler['x_mean']))
                 / np.asarray(scaler['x_scale'])).astype(np.float32)
            model.eval()
            with torch.no_grad():
                value = model(torch.from_numpy(x)).item()
            origin = data['origins'][-1]
            transformed = value * scaler['y_scale'] + scaler['y_mean']
            predicted_log = invert_one_step(
                transformed, data['logs'][:origin + 1], payload['weights'],
            )
            expected = np.expm1(predicted_log - data['logs'][origin])
            self.assertAlmostEqual(
                expected, forecasts[(data['dates'][origin], '600001.SH')], places=10,
            )
            self.assertEqual(metadata['selection_metric'], 'return_mae')


class TuningContractTests(SimpleTestCase):
    def test_search_budget_and_cutoff(self):
        from research.fractional_tuning import SearchSettings

        SearchSettings().validate(date(2016, 10, 14))
        for settings in (
            SearchSettings(total_trials=3), SearchSettings(stock_count=0),
            SearchSettings(fold_years=(2014, 2013)),
            SearchSettings(fold_years=(2014,)), SearchSettings(max_epochs=121),
        ):
            with self.subTest(settings=settings):
                with self.assertRaises(DifferencingError):
                    settings.validate(date(2016, 10, 14))
        with self.assertRaises(DifferencingError):
            SearchSettings().validate(date(2014, 1, 1))

    def test_zero_baseline_normalization_is_explicit(self):
        from research.fractional_tuning import relative_mae

        self.assertAlmostEqual(relative_mae([0.1, -0.1], [0.0, 0.0]), 1.0)
        with self.assertRaises(DifferencingError):
            relative_mae([0.0], [0.0])

    def test_runner_defaults_and_explicit_legacy(self):
        from tools.run_fractional_research import build_parser

        parser = build_parser()
        args = parser.parse_args(['--output', 'new.json'])
        self.assertEqual(args.training_mode, 'tuned')
        self.assertEqual(args.search_trials, 20)
        self.assertEqual(args.epochs, None)
        self.assertEqual(args.early_stopping_patience, 15)
        legacy = parser.parse_args([
            '--output', 'legacy.json', '--training-mode', 'legacy',
        ])
        self.assertEqual(legacy.training_mode, 'legacy')

    def test_runner_refuses_to_overwrite_an_unrelated_model_directory(self):
        from tools.run_fractional_research import build_parser, run

        with TemporaryDirectory() as directory:
            root = Path(directory)
            models = root / 'models'
            models.mkdir()
            args = build_parser().parse_args([
                '--output', str(root / 'new.json'), '--model-directory', str(models),
            ])
            with self.assertRaisesRegex(DifferencingError, 'Model directory already exists'):
                run(args)

    def test_fold_preprocessing_is_train_only_and_ignores_future_prices(self):
        from research.fractional_tuning import prepare_fold

        frame, config = small_prices()
        with patch('research.fractional_tuning.estimate_order', return_value={'order': 1.0}) as estimate:
            original = prepare_fold(frame, config, 'de_prado')
            expected = np.log(frame.loc[frame['date'] < config.validation_start, 'close'])
            np.testing.assert_array_equal(estimate.call_args.args[0], expected)
        changed = frame.copy()
        columns = ['open', 'high', 'low', 'close']
        changed.loc[changed['date'] >= config.test_start, columns] *= 3
        future = prepare_fold(changed, config, 'log_return')
        self.assertEqual(original['metadata']['scaler'], future['metadata']['scaler'])
        np.testing.assert_array_equal(original['data']['x'], future['data']['x'])
        changed.loc[changed['date'] >= config.validation_start, columns] *= 2
        validation = prepare_fold(changed, config, 'log_return')
        self.assertEqual(original['metadata']['scaler'], validation['metadata']['scaler'])
        np.testing.assert_array_equal(
            original['data']['x'][original['train_indices']],
            validation['data']['x'][validation['train_indices']],
        )
        np.testing.assert_array_equal(
            original['data']['y'][original['train_indices']],
            validation['data']['y'][validation['train_indices']],
        )

    @skipUnless(importlib.util.find_spec('torch') and importlib.util.find_spec('optuna'),
                'Optional research dependencies: torch and optuna')
    def test_durable_search_resume_budget_signature_and_best_models(self):
        from research.fractional_tuning import (
            SearchSettings, prepare_fold, run_search, verify_search_artifacts,
        )

        frame, config = small_prices()
        prepared = prepare_fold(frame, config, 'log_return')
        settings = SearchSettings(stock_count=1, total_trials=8, max_epochs=1)
        with TemporaryDirectory() as directory:
            database, root = Path(directory) / 'data.db', Path(directory) / 'search'
            database.touch()
            with patch('research.fractional_tuning.load_fractional_database',
                       return_value=(frame, None, {})), patch(
                'research.fractional_tuning.prepare_fold', return_value=prepared,
            ):
                first = run_search(database, root, settings)
                verify_search_artifacts(root, first)
                again = run_search(database, root, settings, resume=True)
                for method in ('de_prado', 'log_return'):
                    self.assertEqual(len(again['methods'][method]['trials']), 4)
                    self.assertEqual(first['methods'][method]['relative_mae'],
                                     again['methods'][method]['relative_mae'])
                with self.assertRaises(DifferencingError):
                    run_search(database, root, settings)
                with self.assertRaises(DifferencingError):
                    run_search(database, root, replace(settings, seed=43), resume=True)
            report = json.loads((root / 'report.json').read_text(encoding='utf-8'))
            self.assertFalse(report['live_trading_eligible'])

    @skipUnless(importlib.util.find_spec('torch') and importlib.util.find_spec('optuna'),
                'Optional research dependencies: torch and optuna')
    def test_tpe_learns_within_the_small_trial_budget(self):
        import optuna
        from research.fractional_tuning import SearchSettings, _search_method

        frame, config = small_prices()
        from research.fractional_tuning import prepare_fold
        prepared = [prepare_fold(frame, config, 'log_return')]
        study = optuna.create_study()
        study.set_user_attr('signature', 'test')
        with TemporaryDirectory() as directory, patch(
            'optuna.samplers.TPESampler', wraps=optuna.samplers.TPESampler,
        ) as sampler:
            _search_method(study, prepared, SearchSettings(
                stock_count=1, total_trials=10, max_epochs=1,
            ), Path(directory))
        self.assertEqual(len(study.trials), 5)
        self.assertEqual(sampler.call_args.kwargs['n_startup_trials'], 4)

    @skipUnless(importlib.util.find_spec('torch') and importlib.util.find_spec('optuna'),
                'Optional research dependencies: torch and optuna')
    def test_interrupted_and_pruned_trials_remain_in_budget(self):
        import optuna
        from research.fractional_tuning import SearchSettings, _search_method, prepare_fold

        frame, config = small_prices()
        prepared = [prepare_fold(frame, config, 'log_return')]
        study = optuna.create_study()
        study.set_user_attr('signature', 'test')
        study.ask()
        pruned = study.ask()
        study.tell(pruned, state=optuna.trial.TrialState.PRUNED)
        with TemporaryDirectory() as directory:
            _search_method(study, prepared, SearchSettings(
                stock_count=1, total_trials=8, max_epochs=1,
            ), Path(directory))
        self.assertEqual(len(study.trials), 4)
        self.assertEqual(study.trials[0].state.name, 'FAIL')
        self.assertEqual(study.trials[1].state.name, 'PRUNED')
        self.assertEqual(study.user_attrs['interrupted_trials'], [0])
    @skipUnless(importlib.util.find_spec('torch'), 'Optional research dependency: torch')
    def test_default_runner_freezes_method_specific_search_and_persists_models(self):
        from research.fractional_forecast import DatabaseRandomUniverse
        from tools.run_fractional_research import build_parser, run

        frame, config = small_prices()
        universe = DatabaseRandomUniverse(['600001.SH'], date.today(), 42, 1)
        settings = {
            'de_prado': LSTMTrial(hidden_size=4, epochs=1),
            'log_return': LSTMTrial(hidden_size=3, epochs=1, num_layers=2),
        }
        search_report = {
            'signature': 'frozen-search',
            'methods': {method: {
                'selected_trial': trial.__dict__, 'qualified_vs_zero_baseline': False,
            } for method, trial in settings.items()},
        }
        with TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / 'data.db'
            database.touch()
            args = build_parser().parse_args([
                '--database', str(database), '--output', str(root / 'result.json'),
                '--walk-forward-validation-days', '5', '--universe-size', '1',
            ])
            with patch('tools.run_fractional_research.ForecastConfig', return_value=config), patch(
                'tools.run_fractional_research.load_fractional_database',
                return_value=(frame, universe, {'selected_instruments': ['600001.SH']}),
            ), patch('research.fractional_tuning.run_search', return_value=search_report) as search, patch(
                'research.fractional_lstm.estimate_order', return_value={'order': 1.0},
            ):
                result = run(args)
            search.assert_called_once()
            self.assertEqual(result['parameters']['training_mode'], 'tuned')
            self.assertEqual(result['parameters']['early_stopping_patience'], 15)
            self.assertEqual(result['hyperparameter_search']['signature'], 'frozen-search')
            for method, trial in settings.items():
                model = result['models'][f'600001.SH:{method}']
                self.assertEqual(model['selected_model']['hidden_size'], trial.hidden_size)
                self.assertEqual(model['selected_model']['num_layers'], trial.num_layers)
                self.assertEqual(model['selection_metric'], 'return_mae')
                self.assertTrue((args.model_directory / f'600001.SH-{method}'
                                 / 'refit-latest.pt').is_file())
            json.dumps(chinese_result(result), allow_nan=False)
