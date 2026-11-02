from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import numpy as np
import pandas as pd

try:
    import torch
except ImportError:
    torch = None

from research.fractional_forecast import fractional_weights
from research.portfolio_lstm import (
    FEATURE_NAMES,
    PortfolioModelConfig,
    build_feature_frame,
    fit_feature_scaler,
    make_position_targets,
    portfolio_growth_loss,
    predict_scores,
    save_model_bundle,
    load_model_bundle,
    select_positions,
    train_shared_model,
    wrap_model_for_training,
)
from research.portfolio_tuning import build_portfolio_panel, simulate_portfolio


def prices(symbol='600001.SH', size=85, *, missing=()):
    sessions = [date(2024, 1, 1) + timedelta(days=index) for index in range(size)]
    close = 50 * np.exp(np.cumsum(0.002 * np.sin(np.arange(size)) + 0.0002))
    rows = []
    for index, day in enumerate(sessions):
        if index in missing:
            continue
        rows.append({
            'date': day, 'instrument': symbol,
            'open': close[index] * .999, 'high': close[index] * 1.01,
            'low': close[index] * .99, 'close': close[index],
            'volume': 100000 + index, 'suspended': False,
        })
    return pd.DataFrame(rows), sessions


class SharedPortfolioModelTests(TestCase):
    def setUp(self):
        if torch is None:
            self.skipTest('Optional research dependency: torch')
        self.trial = {
            'hidden_size': 8, 'num_layers': 1, 'dropout': 0.0, 'batch_size': 4,
            'learning_rate': .001,
        }
        self.config = PortfolioModelConfig(**self.trial, sequence_length=10)

    def test_feature_transform_is_causal_and_fractional_weights_are_fixed(self):
        frame, sessions = prices()
        weights = fractional_weights(1.0)
        first = build_feature_frame(frame, sessions, weights)
        changed = frame.copy()
        changed.loc[changed.index[-1], ['open', 'high', 'low', 'close', 'volume']] *= 10
        second = build_feature_frame(changed, sessions, weights)
        pd.testing.assert_frame_equal(
            first.iloc[:-1][list(FEATURE_NAMES)],
            second.iloc[:-1][list(FEATURE_NAMES)],
        )
        reordered = build_feature_frame(
            frame.iloc[::-1], sessions, weights,
        )
        pd.testing.assert_frame_equal(
            first[list(FEATURE_NAMES)], reordered[list(FEATURE_NAMES)],
        )
        self.assertEqual(len(weights), 2)

    def test_gap_breaks_sequences_instead_of_interpolating_or_crossing(self):
        frame, sessions = prices(size=100, missing=(65,))
        transformed = build_feature_frame(frame, sessions, fractional_weights(1.0))
        after_gap = transformed.index[transformed['date'] == sessions[66]][0]
        self.assertTrue(transformed.loc[after_gap, list(FEATURE_NAMES)].isna().all())
        self.assertTrue(transformed.loc[after_gap + 21, list(FEATURE_NAMES)].notna().all())
        self.assertFalse(any(day == sessions[65] for day in transformed['date']))

    def test_suspension_bar_breaks_segments_and_never_becomes_a_label(self):
        frame, sessions = prices(size=100)
        frame.loc[frame['date'] == sessions[65], 'suspended'] = True
        transformed = build_feature_frame(frame, sessions, fractional_weights(1.0))
        after_gap = transformed.index[transformed['date'] == sessions[66]][0]
        self.assertTrue(transformed.loc[after_gap, list(FEATURE_NAMES)].isna().all())

    def test_global_scaler_only_uses_supplied_training_sequences(self):
        training = np.ones((3, 10, len(FEATURE_NAMES)), dtype=np.float32)
        validation = np.full((2, 10, len(FEATURE_NAMES)), 100, dtype=np.float32)
        scaler = fit_feature_scaler(training)
        self.assertEqual(scaler['mean'], [1.0] * len(FEATURE_NAMES))
        normalized = (validation - scaler['mean']) / scaler['scale']
        self.assertTrue((normalized > 50).all())

    def test_position_targets_cap_slots_and_keep_empty_slots_in_cash(self):
        scores = {f'{index:06d}.SH': 1.0 - index / 1000 for index in range(40)}
        targets = select_positions(scores, previous={}, eligible=set(scores))
        self.assertEqual(len(targets), 30)
        self.assertAlmostEqual(sum(targets.values()), .95)
        self.assertTrue(all(weight == .95 / 30 for weight in targets.values()))
        few = select_positions(dict(list(scores.items())[:2]), previous={}, eligible=set(scores))
        self.assertAlmostEqual(sum(few.values()), 2 * .95 / 30)

    def test_position_targets_preserve_threshold_hysteresis_and_ignore_ineligible(self):
        targets = select_positions(
            {'a': .003, 'b': 0, 'c': -.003, 'd': .1},
            previous={'a': .95 / 30, 'b': .95 / 30, 'c': .95 / 30},
            eligible={'a', 'b', 'c'},
        )
        self.assertEqual(set(targets), {'a', 'b'})

    def test_soft_portfolio_objective_is_finite_differentiable_and_cost_aware(self):
        scores = torch.tensor([[.004, .003, -.004]], requires_grad=True)
        returns = torch.tensor([[.02, -.01, .5]])
        eligible = torch.tensor([[True, True, False]])
        previous = torch.zeros_like(scores)
        config = PortfolioModelConfig(**self.trial, sequence_length=10)
        loss = portfolio_growth_loss(scores, returns, eligible, previous, config)
        loss.backward()
        self.assertTrue(torch.isfinite(loss))
        self.assertTrue(torch.isfinite(scores.grad).all())
        self.assertGreater(torch.count_nonzero(scores.grad).item(), 0)
        occupied = float(make_position_targets(
            scores.detach(), eligible, previous, config,
        ).sum())
        self.assertGreater(occupied, .95 / 30)
        self.assertLess(occupied, config.exposure)

    def test_training_loop_uses_shared_sequences_and_reports_surrogate_only(self):
        from research.portfolio_lstm import SharedPortfolioLSTM

        config = PortfolioModelConfig(
            **self.trial, sequence_length=10, max_epochs=1, patience=0,
        )
        model = SharedPortfolioLSTM(len(FEATURE_NAMES), config)
        batch = {
            'sequences': torch.randn(2, 3, 10, len(FEATURE_NAMES)),
            'returns': torch.tensor([[.01, -.01, .02], [.0, .01, -.02]]),
            'eligible': torch.ones(2, 3, dtype=torch.bool),
            'previous': torch.zeros(2, 3),
        }
        result = train_shared_model(model, [batch], config)
        self.assertEqual(result['epochs_completed'], 1)
        self.assertTrue(np.isfinite(result['minimum_training_loss']))
        self.assertTrue(result['validation_required_for_model_selection'])
        self.assertFalse(result['selected'])

    def test_training_model_uses_both_available_cuda_devices(self):
        if torch.cuda.device_count() < 2:
            self.skipTest('Two CUDA devices are not available')
        from research.portfolio_lstm import SharedPortfolioLSTM

        config = PortfolioModelConfig(**self.trial, sequence_length=10)
        base = SharedPortfolioLSTM(len(FEATURE_NAMES), config).to('cuda:0')
        model = wrap_model_for_training(base, torch.device('cuda:0'))
        self.assertIsInstance(model, torch.nn.DataParallel)
        self.assertEqual(model.device_ids, [0, 1])
        values = torch.randn(4, 10, len(FEATURE_NAMES), device='cuda:0')
        model.eval()
        with torch.no_grad():
            model(values)
        model.train()
        scores = model(values)
        self.assertEqual(tuple(scores.shape), (4,))
        scores.sum().backward()
        self.assertTrue(all(
            parameter.grad is not None
            and torch.isfinite(parameter.grad).all()
            for parameter in base.parameters()
        ))

    def test_validation_selection_never_accepts_drawdown_breach(self):
        from research.portfolio_lstm import SharedPortfolioLSTM

        config = PortfolioModelConfig(
            **self.trial, sequence_length=10, max_epochs=2, patience=0,
        )
        model = SharedPortfolioLSTM(len(FEATURE_NAMES), config)
        batch = {
            'sequences': torch.randn(1, 2, 10, len(FEATURE_NAMES)),
            'returns': torch.tensor([[.01, -.01]]),
            'eligible': torch.ones(1, 2, dtype=torch.bool),
            'previous': torch.zeros(1, 2),
        }
        results = iter((
            {'portfolio_return': .50, 'max_drawdown_by_year': {'2024': .21}},
            {'portfolio_return': .10, 'max_drawdown_by_year': {'2024': .20}},
        ))
        selected = train_shared_model(
            model, [batch], config, lambda *_: next(results), validation_years=['2024'],
        )
        self.assertTrue(selected['selected'])
        self.assertFalse(selected['validation_required_for_model_selection'])
        self.assertEqual(selected['best_validation_portfolio_return'], .10)
        self.assertFalse(selected['history'][0]['validation']['passed_drawdown_gate'])
        self.assertTrue(selected['history'][1]['validation']['passed_drawdown_gate'])
        with self.assertRaisesRegex(ValueError, 'configured years'):
            train_shared_model(
                model, [batch], config,
                lambda *_: {
                    'portfolio_return': .1,
                    'max_drawdown_by_year': {'2024': .1},
                },
                validation_years=['2023', '2024'],
            )

    def test_panel_respects_training_only_scaler_and_discrete_simulation(self):
        frame, sessions = prices(size=55, missing=(31,))
        suspended = {'600001.SH': {sessions[31].strftime('%Y%m%d')}}
        validation_start = sessions[40]
        panel = build_portfolio_panel(
            frame, sessions, suspended, ['600001.SH'],
            {'600001.SH': fractional_weights(1.0).tolist()},
            train_start=sessions[0], validation_start=validation_start,
            sequence_length=10,
        )
        self.assertFalse(panel.eligible[30, 0])
        self.assertFalse(panel.feature_valid[32, 0])
        self.assertGreater(panel.scaler['mean'][0], 0)
        config = PortfolioModelConfig(**self.trial, sequence_length=10)
        scores = np.full((len(sessions), 1), .01, dtype=np.float32)
        metrics = simulate_portfolio(
            panel, scores, range(10, 40), config,
        )
        self.assertEqual(len(metrics['curve']), 30)
        self.assertLessEqual(metrics['max_drawdown'], 1.0)
        self.assertGreaterEqual(metrics['fees'], 0)

    def test_bundle_round_trip_validates_state_and_inference_scores(self):
        from research.portfolio_lstm import SharedPortfolioLSTM

        model = SharedPortfolioLSTM(len(FEATURE_NAMES), self.config)
        symbols = ['600001.SH']
        metadata = {
            'run_id': 'run-test', 'method': 'log_return', 'epoch': 3,
            'selection_metric': 'validation_portfolio_return_subject_to_drawdown',
            'training_status': 'synthetic_test_only',
            'validation': {'passed': False, 'max_drawdown_limit': .20,
                           'max_drawdown_by_year': {}},
        }
        scaler = {'mean': [0.0] * len(FEATURE_NAMES),
                  'scale': [1.0] * len(FEATURE_NAMES)}
        weights = {'600001.SH': fractional_weights(1).tolist()}
        with TemporaryDirectory() as temp:
            directory = Path(temp) / 'bundle'
            save_model_bundle(directory, model, self.config, symbols, weights,
                              scaler, 'a' * 64, metadata)
            bundle = load_model_bundle(directory, map_location='cpu')
            self.assertEqual(bundle.manifest['universe_signature'], 'a' * 64)
            self.assertFalse(bundle.manifest['live_trading_eligible'])
            frame, sessions = prices(size=65)
            scores, exclusions = predict_scores(
                bundle, {'600001.SH': frame}, sessions, sessions[-1],
            )
            self.assertEqual(set(scores), {'600001.SH'})
            self.assertFalse(exclusions)
            self.assertTrue(np.isfinite(scores['600001.SH']))
            self.assertFalse((directory / 'model.pt.tmp').exists())

    def test_bundle_refuses_overwrite_tampering_and_unknown_symbol_specs(self):
        from research.portfolio_lstm import SharedPortfolioLSTM

        model = SharedPortfolioLSTM(len(FEATURE_NAMES), self.config)
        metadata = {'run_id': 'run-test', 'method': 'log_return', 'epoch': 1,
                    'training_status': 'synthetic_test_only',
                    'validation': {'passed': False, 'max_drawdown_limit': .20,
                                   'max_drawdown_by_year': {}}}
        scaler = {'mean': [0.0] * len(FEATURE_NAMES),
                  'scale': [1.0] * len(FEATURE_NAMES)}
        with TemporaryDirectory() as temp:
            directory = Path(temp) / 'bundle'
            save_model_bundle(directory, model, self.config, ['600001.SH'],
                              {'600001.SH': [1.0, -1.0]}, scaler, 'b' * 64, metadata)
            with self.assertRaisesRegex(ValueError, 'already exists'):
                save_model_bundle(directory, model, self.config, ['600001.SH'],
                                  {'600001.SH': [1.0, -1.0]}, scaler, 'b' * 64, metadata)
            with (directory / 'model.pt').open('ab') as stream:
                stream.write(b'tamper')
            with self.assertRaisesRegex(ValueError, 'SHA256'):
                load_model_bundle(directory)
        with TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, 'symbols'):
                save_model_bundle(
                    Path(temp) / 'bundle', model, self.config, ['600001.SH'],
                    {}, scaler, 'b' * 64, metadata,
                )

    def test_inference_fails_closed_for_unknown_and_missing_as_of_prices(self):
        from research.portfolio_lstm import SharedPortfolioLSTM

        model = SharedPortfolioLSTM(len(FEATURE_NAMES), self.config)
        with TemporaryDirectory() as temp:
            directory = Path(temp) / 'bundle'
            save_model_bundle(
                directory, model, self.config, ['600001.SH'],
                {'600001.SH': fractional_weights(1).tolist()},
                {'mean': [0.] * len(FEATURE_NAMES), 'scale': [1.] * len(FEATURE_NAMES)},
                'c' * 64,
                {'run_id': 'run-test', 'method': 'log_return', 'epoch': 1,
                 'training_status': 'synthetic_test_only',
                 'validation': {'passed': False, 'max_drawdown_limit': .20,
                                'max_drawdown_by_year': {}}},
            )
            bundle = load_model_bundle(directory)
            frame, sessions = prices(size=65)
            with self.assertRaisesRegex(ValueError, 'unknown model symbols'):
                predict_scores(bundle, {'not-selected.SH': frame}, sessions, sessions[-1])
            missing = frame[frame['date'] != sessions[-1]]
            _, excluded = predict_scores(
                bundle, {'600001.SH': missing}, sessions, sessions[-1],
            )
            self.assertIn('no tradable quote on as_of session', excluded['600001.SH'])
