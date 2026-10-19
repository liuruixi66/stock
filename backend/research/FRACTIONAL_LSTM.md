# Database-backed fractional LSTM research

Run the experiment from `backend` so Python resolves the `research` package:

```powershell
python -m tools.run_fractional_research --output .\fractional-lstm-results.json
```

The runner reads `stocks.db` in read-only mode and does not download prices. It selects a reproducible sample of 30 Shanghai non-ETF stocks with complete adjusted daily data across the configured training, validation, and test ranges. The database does not contain historical SSE 50 membership, so this sample is not an SSE 50 replication and has survivorship bias.

Before training, SQLite scans the historical data to find eligible stocks. This CPU/disk stage can take several minutes on a large database and does not use the GPU. The CLI logs each loading stage and emits a heartbeat roughly every ten seconds while SQLite executes a long query; these messages indicate activity, not a completion percentage.

By default, training uses data from 2006-10-16 through the validation start of 2014-10-14; validation runs through 2016-10-13; and the out-of-sample test spans 2016-10-14 through 2026-10-14. Override the split dates with `--train-start`, `--validation-start`, `--test-start`, and `--test-end` when using a database with different coverage.

When CUDA is available, training starts on GPU 0. A CUDA out-of-memory error on that run retries the model with `DataParallel` across GPUs 0 and 1, if both are visible. Without CUDA, training uses the CPU. If one or both GPU attempts run out of memory, the run stops with an explicit error instead of silently falling back to a different device. Each model's output metadata records the training device, visible GPU names, whether the two-GPU fallback ran, and the fallback GPU IDs.

The experiment trains both De Prado fractional differencing and first-difference branches, evaluates only on dates after each model's training and validation periods, and writes the result once without overwriting an existing output file. Install the optional research dependencies in the Python environment before running it, including PyTorch and `statsmodels`.
