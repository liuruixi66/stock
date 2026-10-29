from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import numpy as np
import torch

from research.rotation_training import (
    ResidentPanel, SharedLSTM, batch_loader, checked_loss, training_step,
)
from tools.benchmark_rotation_training import render_report


class RotationBatchingTests(TestCase):
    def test_performance_report_discloses_measurement_scope(self):
        run = {
            backend: {
                'seconds': seconds, 'samples_per_second': 300 / seconds,
                'gpu_utilization': {
                    '0': {'mean_percent': 20, 'samples': 10},
                    '1': {'mean_percent': 30, 'samples': 10},
                },
            }
            for backend, seconds in (('legacy', 3), ('resident', 2))
        }
        run['max_absolute_weight_error'] = 0.
        with TemporaryDirectory() as directory:
            output = Path(directory)
            render_report(output, {
                'runs': [run], 'speedup': 1.5, 'steps_per_phase': 0, 'repeats': 1,
            })
            html = (output / 'index.html').read_text(encoding='utf-8')
            self.assertIn('1.50', html)
            self.assertIn('完整训练集＋验证集', html)
            self.assertIn('不是 CUDA 核心占用率', html)
            self.assertIn('不含一次性特征处理', html)
            for backend in ('legacy', 'resident'):
                del run[backend]['gpu_utilization']
            render_report(output, {
                'runs': [run], 'speedup': 1.5, 'steps_per_phase': 3, 'repeats': 1,
            })
            self.assertIn('未采样', (output / 'index.html').read_text(encoding='utf-8'))

    def panel(self):
        rng = np.random.default_rng(42)
        return {
            'features': rng.normal(size=(90, 5)).astype(np.float32),
            'ends': np.arange(19, 90, dtype=np.int64),
            'y': rng.normal(size=71).astype(np.float32),
            'target_mean': .0123, 'target_scale': .052,
        }

    def test_batch_values_order_rng_and_last_batch_are_preserved(self):
        panel = self.panel()
        indices = np.arange(71)
        resident = ResidentPanel(panel, 20, torch.device('cpu'))
        for shuffle in (False, True):
            torch.manual_seed(55)
            legacy = list(batch_loader(panel, indices, 20, 16, shuffle))
            legacy_rng = torch.random.get_rng_state()
            torch.manual_seed(55)
            optimized = list(batch_loader(panel, indices, 20, 16, shuffle, resident))
            self.assertEqual(len(legacy), 5)
            self.assertEqual(len(optimized[-1][0]), 7)
            for old_batch, new_batch in zip(legacy, optimized):
                for old, new in zip(old_batch, new_batch):
                    torch.testing.assert_close(old, new, rtol=0, atol=0)
            torch.testing.assert_close(torch.random.get_rng_state(), legacy_rng, rtol=0, atol=0)
        self.assertEqual(resident.features.shape, (90, 5))

    def test_shared_model_checkpoint_and_optimizer_update_match(self):
        panel = self.panel()
        resident = ResidentPanel(panel, 20, torch.device('cpu'))
        states = []
        for optimized in (False, True):
            torch.manual_seed(42)
            model = SharedLSTM()
            optimizer = torch.optim.Adam(model.parameters(), lr=.001)
            loader = batch_loader(panel, np.arange(71), 20, 16, False,
                                  resident if optimized else None)
            for x, y, _ in loader:
                if optimized:
                    loss = training_step(model, optimizer, torch.nn.MSELoss(), x, y)
                else:
                    optimizer.zero_grad()
                    loss = torch.nn.functional.mse_loss(model(x), y)
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 1., error_if_nonfinite=True)
                    optimizer.step()
                self.assertTrue(torch.isfinite(loss))
            states.append(model.state_dict())
        self.assertIn('lstm.weight_ih_l0', states[0])
        for key in states[0]:
            torch.testing.assert_close(states[0][key], states[1][key], rtol=0, atol=0)

    def test_nonfinite_loss_is_explicit(self):
        for value in (float('nan'), float('inf')):
            with self.assertRaisesRegex(ValueError, 'Non-finite'):
                checked_loss(torch.tensor(value))
        checked_loss(torch.tensor(1.))
