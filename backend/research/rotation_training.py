"""Batching and model helpers shared by training and its performance benchmark."""

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset


class SharedLSTM(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(5, 32, batch_first=True)
        self.head = nn.Linear(32, 1)

    def forward(self, inputs):
        output, _ = self.lstm(inputs)
        return self.head(output[:, -1]).squeeze(-1)


class SequenceSamples(Dataset):
    def __init__(self, panel, indices, sequence_length):
        self.panel = panel
        self.indices = indices
        self.sequence_length = sequence_length

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, position):
        index = self.indices[position]
        end = self.panel['ends'][index]
        x = self.panel['features'][end - self.sequence_length + 1:end + 1]
        y = (self.panel['y'][index] - self.panel['target_mean']) / self.panel['target_scale']
        return x, np.float32(y), index


class ResidentPanel:
    """Keep compact feature rows on device, gather only the current sequences."""

    def __init__(self, panel, sequence_length, device):
        self.features = torch.as_tensor(np.ascontiguousarray(panel['features']), device=device)
        self.ends = torch.as_tensor(panel['ends'], dtype=torch.long, device=device)
        normalized = ((panel['y'] - panel['target_mean']) / panel['target_scale']).astype(np.float32)
        self.targets = torch.as_tensor(normalized, device=device)
        self.offsets = torch.arange(1 - sequence_length, 1, device=device)
        self.device = device

    def gather(self, indices):
        device_indices = indices.to(self.device, non_blocking=True)
        rows = self.ends[device_indices, None] + self.offsets
        return self.features[rows], self.targets[device_indices], indices


class ResidentBatches:
    def __init__(self, resident, indices, batch_size, shuffle):
        # Retain DataLoader's RNG, shuffle and last-batch semantics exactly.
        self.loader = DataLoader(indices, batch_size=batch_size, shuffle=shuffle,
                                 num_workers=0, pin_memory=resident.device.type == 'cuda')
        self.dataset = self.loader.dataset
        self.resident = resident

    def __len__(self):
        return len(self.loader)

    def __iter__(self):
        for indices in self.loader:
            yield self.resident.gather(indices)


def batch_loader(panel, indices, sequence_length, batch_size, shuffle=False, resident=None):
    if resident is not None:
        return ResidentBatches(resident, indices, batch_size, shuffle)
    return DataLoader(SequenceSamples(panel, indices, sequence_length),
                      batch_size=batch_size, shuffle=shuffle, num_workers=0)


def checked_loss(loss):
    # CUDA assertion is stream-ordered and does not copy a scalar to the CPU.
    if loss.device.type == 'cuda':
        torch._assert_async(torch.isfinite(loss), 'Non-finite model loss')
    elif not torch.isfinite(loss):
        raise ValueError('Non-finite model loss')


def training_step(model, optimizer, loss_function, x, y):
    optimizer.zero_grad()
    loss = loss_function(model(x), y)
    checked_loss(loss)
    loss.backward()
    norm = nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=False)
    checked_loss(norm)
    optimizer.step()
    return loss.detach()
