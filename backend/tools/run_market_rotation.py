"""Train a shared five-session LSTM and report independent weekly rotation."""

import argparse
from contextlib import closing
from dataclasses import asdict
from datetime import date, datetime
import json
import logging
from pathlib import Path
import sqlite3
import sys
import time

from config.settings import STOCKS_DATABASE_PATH
from research.market_rotation import RotationConfig, prepare_panel, simulate_rotation


logger = logging.getLogger(__name__)
LIMITATIONS = [
    'ST exclusion disabled by user; empty name history does not prove non-ST status.',
    'Industry cap disabled by user; no historical industry classification is inferred.',
    'TWAP/VWAP unavailable: no intraday timestamps, prices and volume history.',
    'Adjusted fractional-unit research, not actual A-share fills or live trading.',
    'Daily open limit-price checks cannot model intraday queues, spread or impact.',
    'Suspended/missing-quote holdings freeze at last adjusted mark; delisting recovery is unknown.',
    'Historical supplier snapshots are not certified point-in-time; backfilled corrections may exist.',
    'Validation selects model epoch and entry threshold; only 2026 is held out from this run.',
    'Previous experiments already inspected 2026; this is not a globally untouched test period.',
    'Five-close return target differs from next-open execution and calendar-week holding length.',
]


def select_device(requested, torch):
    if requested == 'auto':
        return torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    if requested == 'cpu':
        return torch.device('cpu')
    if not requested.startswith('cuda:') or not requested[5:].isdigit():
        raise ValueError('Device must be auto, cpu or cuda:N')
    index = int(requested[5:])
    if not torch.cuda.is_available() or index >= torch.cuda.device_count():
        raise ValueError(f'Requested GPU unavailable: {requested}; CPU fallback is disabled')
    return torch.device(requested)


def parallel_devices(requested, device_ids, torch):
    if not device_ids:
        return select_device(requested, torch), []
    if requested != 'auto':
        raise ValueError('Use either --device or --gpu-ids, not both')
    if (len(device_ids) < 2 or len(set(device_ids)) != len(device_ids)
            or any(index < 0 for index in device_ids)):
        raise ValueError('Parallel training requires at least two unique GPU indices')
    for index in device_ids:
        select_device(f'cuda:{index}', torch)
    return torch.device(f'cuda:{device_ids[0]}'), list(device_ids)


def replace_report_file(temporary, path):
    # Windows readers/indexers may briefly hold the old report open.
    for attempt in range(6):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt == 5:
                raise
            logger.warning('Report file is temporarily locked; retrying %s', path)
            time.sleep(0.1 * (attempt + 1))


def save_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2),
                         encoding='utf-8')
    replace_report_file(temporary, path)


def report(directory, state):
    from tools.market_rotation_dashboard import render_dashboard

    save_json(directory / 'progress.json', state)
    content = render_dashboard(state)
    temporary = directory / 'index.html.tmp'
    temporary.write_text(content, encoding='utf-8')
    replace_report_file(temporary, directory / 'index.html')


def load_market(database, config, symbol_limit=0, progress=None):
    import numpy as np
    import pandas as pd

    with closing(sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)) as conn:
        conn.execute('BEGIN')
        # Snapshot is fixed by the first read, even while the collector updates.
        ends = {
            table: conn.execute(f'SELECT MAX(trade_date) FROM {table}').fetchone()[0]
            for table in ('ts_daily', 'ts_adj_factor', 'ts_stk_limit', 'ts_suspend_d')
        }
        if any(value is None for value in ends.values()):
            raise ValueError(f'Empty required market source: {ends}')
        end_raw = min(ends.values())
        end = datetime.strptime(end_raw, '%Y%m%d').date().isoformat()
        if end < config.test_start:
            raise ValueError('Market sources do not cover the held-out test period')
        sessions = [
            datetime.strptime(row[0], '%Y%m%d').date().isoformat()
            for row in conn.execute(
                '''SELECT cal_date FROM ts_trade_cal WHERE exchange='SSE'
                   AND is_open=1 AND cal_date BETWEEN ? AND ? ORDER BY cal_date''',
                (config.train_start.replace('-', ''), end_raw),
            )
        ]
        if not sessions or sessions[-1] != end:
            raise ValueError('Trading calendar does not cover the source end date')
        session_set = set(sessions)
        suspensions = set(conn.execute(
            '''SELECT ts_code,trade_date FROM ts_suspend_d
               WHERE suspend_type='S' AND trade_date BETWEEN ? AND ?''',
            (config.train_start.replace('-', ''), end_raw),
        ))
        universe = conn.execute(
            '''SELECT ts_code,list_date,delist_date FROM ts_stock_basic
               WHERE exchange IN ('SSE','SZSE')
                 AND substr(ts_code,1,1) IN ('0','3','6')
                 AND length(ts_code)=9 AND substr(ts_code,1,6) NOT GLOB '*[^0-9]*'
                 AND list_date <= ?
                 AND (delist_date IS NULL OR delist_date='' OR delist_date >= ?)
               ORDER BY ts_code''',
            (end_raw, config.train_start.replace('-', '')),
        ).fetchall()
        if symbol_limit:
            # Distributed deterministic smoke subset, never called full market.
            positions = np.linspace(0, len(universe) - 1,
                                    min(symbol_limit, len(universe)), dtype=int)
            universe = [universe[i] for i in positions]
        if not universe:
            raise ValueError('No Shanghai/Shenzhen A-share universe found')
        frames = []
        for index, (symbol, listing, delisting) in enumerate(universe):
            rows = conn.execute(
                '''SELECT d.trade_date,d.open,d.high,d.low,d.close,d.vol,
                          a.adj_factor,l.up_limit,l.down_limit
                   FROM ts_daily d
                   LEFT JOIN ts_adj_factor a ON a.ts_code=d.ts_code
                                           AND a.trade_date=d.trade_date
                   LEFT JOIN ts_stk_limit l ON l.ts_code=d.ts_code
                                          AND l.trade_date=d.trade_date
                   WHERE d.ts_code=? AND d.trade_date BETWEEN ? AND ?
                   ORDER BY d.trade_date''',
                (symbol, max(config.train_start.replace('-', ''), listing),
                 min(end_raw, delisting) if delisting else end_raw),
            ).fetchall()
            if not rows:
                raise ValueError(f'Missing listed-stock history for {symbol}')
            frame = pd.DataFrame(rows, columns=[
                'raw_day', 'open', 'high', 'low', 'close', 'volume', 'factor',
                'up_limit', 'down_limit',
            ])
            frame['suspended'] = [
                (symbol, raw_day) in suspensions for raw_day in frame['raw_day']
            ]
            frame['day'] = pd.to_datetime(frame.pop('raw_day'), format='%Y%m%d').dt.strftime('%Y-%m-%d')
            frame['symbol'] = symbol
            numeric = frame[['open', 'high', 'low', 'close', 'volume', 'factor']].to_numpy(dtype=float)
            if (not np.isfinite(numeric).all() or (numeric[:, :4] <= 0).any()
                    or (numeric[:, 4] < 0).any() or (numeric[:, 5] <= 0).any()
                    or (frame['low'] > frame[['open', 'close']].min(axis=1)).any()
                    or (frame['high'] < frame[['open', 'close']].max(axis=1)).any()):
                raise ValueError(f'Invalid OHLC/volume/adjustment for {symbol}')
            if not set(frame['day']) <= session_set:
                raise ValueError(f'Quote outside trading calendar for {symbol}')
            # Limitless listing days are not guessed tradable. NaN bounds mean
            # no execution, with explicit counts in the provenance.
            frame['limit_missing'] = frame[['up_limit', 'down_limit']].isna().any(axis=1)
            frame.loc[frame['limit_missing'], 'suspended'] = True
            frames.append(frame)
            if (index + 1) % 100 == 0 or index + 1 == len(universe):
                logger.info('Loaded %d / %d stocks', index + 1, len(universe))
                if progress:
                    progress(index + 1, len(universe))
        panel = pd.concat(frames, ignore_index=True)
    provenance = {
        'database': str(database.resolve()), 'source_ends': ends, 'effective_end': end,
        'symbols': len(universe), 'rows': len(panel), 'smoke_subset': bool(symbol_limit),
        'missing_limit_rows_frozen': int(panel['limit_missing'].sum()),
        'snapshot_policy': 'single SQLite read transaction; inputs exported before training',
        'st_filter': False, 'industry_cap': False, 'twap_vwap': 'insufficient_intraday_data',
    }
    return panel, sessions, provenance


def run(args, state, update):
    import numpy as np
    import pandas as pd
    import torch
    from torch import nn

    from research.prediction_metrics import evaluate_return_predictions
    from research.rotation_training import (
        ResidentPanel, SharedLSTM, batch_loader, checked_loss, training_step,
    )

    config = RotationConfig()
    config.validate()
    torch.manual_seed(42)
    np.random.seed(42)
    torch.set_num_threads(args.threads)
    device, device_ids = parallel_devices(args.device, args.gpu_ids, torch)
    state['parallel_mode'] = 'DataParallel' if device_ids else 'single_device'
    state['gpu_ids'] = device_ids
    state['gpu_names'] = [torch.cuda.get_device_name(index) for index in device_ids]
    if device.type == 'cuda':
        torch.cuda.set_device(device)
        # Verify CUDA computation before loading a large database snapshot.
        probe = torch.ones(2, 2, device=device)
        (probe @ probe).sum().item()
        state['gpu_name'] = torch.cuda.get_device_name(device)
        state['cuda_runtime'] = torch.version.cuda
    state['python_executable'] = sys.executable
    state['torch_version'] = str(torch.__version__)
    state['device'] = str(device)
    state['config'] = asdict(config)
    state['status'] = 'loading_frozen_market_snapshot'
    update()
    def loading_progress(loaded, total):
        state['loading'] = {'loaded': loaded, 'total': total}
        update()

    prices, sessions, provenance = load_market(
        args.database, config, args.symbol_limit, loading_progress,
    )
    state['provenance'] = provenance
    prices.to_pickle(args.output_directory / 'market-snapshot.pkl')
    save_json(args.output_directory / 'sessions.json', sessions)
    state['status'] = 'preparing_sequences'
    update()
    panel = prepare_panel(prices, sessions, config)
    save_json(args.output_directory / 'scaler.json', {
        'mean': panel['mean'].tolist(), 'scale': panel['scale'].tolist(),
        'target_mean': panel['target_mean'], 'target_scale': panel['target_scale'],
        'fit_partition': 'train_only',
    })
    state['samples'] = {name: int(mask.sum()) for name, mask in panel['masks'].items()}
    state['status'] = 'training'
    update()

    backend = args.batch_backend
    if backend == 'auto':
        backend = 'resident' if device.type == 'cuda' else 'legacy'
    resident = (ResidentPanel(panel, config.sequence_length, device)
                if backend == 'resident' else None)
    state['batch_backend'] = backend
    state['precision'] = 'float32'
    state['batch_size'] = args.batch_size

    def loader(indices, shuffle=False):
        return batch_loader(panel, indices, config.sequence_length,
                            args.batch_size, shuffle, resident)

    base_model = SharedLSTM().to(device)
    model = (nn.DataParallel(base_model, device_ids=device_ids,
                             output_device=device_ids[0]) if device_ids else base_model)
    state['model_device'] = str(next(model.parameters()).device)
    logger.info('Shared LSTM device: %s (%s)', state['model_device'],
                state.get('gpu_name', 'CPU'))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_function = nn.MSELoss()
    train_loader = loader(np.flatnonzero(panel['masks']['train']), True)
    validation_loader = loader(np.flatnonzero(panel['masks']['validation']))
    if device_ids and min(args.batch_size, len(train_loader.dataset)) < len(device_ids):
        raise ValueError('First training batch must contain enough samples for every GPU')
    best_loss = float('inf')
    for epoch in range(args.epochs):
        model.train()
        total = torch.zeros((), device=device) if resident is not None else 0.0
        count = 0
        started = time.monotonic()
        for batch, (x, y, _) in enumerate(train_loader):
            x, y = x.to(device), y.to(device)
            if resident is None:
                optimizer.zero_grad()
            observed = []
            hook = (base_model.lstm.register_forward_hook(
                lambda module, inputs, output: observed.append(str(output[0].device)),
            ) if device_ids and epoch == 0 and batch == 0 else None)
            try:
                if resident is not None:
                    loss = training_step(model, optimizer, loss_function, x, y)
                else:
                    loss = loss_function(model(x), y)
                    if not torch.isfinite(loss):
                        raise ValueError('Non-finite training loss')
                    loss.backward()
            finally:
                if hook is not None:
                    hook.remove()
            if hook is not None:
                expected = {f'cuda:{index}' for index in device_ids}
                if set(observed) != expected:
                    raise RuntimeError(f'Not all requested GPUs computed LSTM output: {observed}')
                state['verified_training_devices'] = sorted(set(observed))
                logger.info('Verified shared-model training on GPUs: %s', observed)
            if resident is None:
                nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
                optimizer.step()
            total += (loss.detach() if resident is not None else float(loss.detach())) * len(x)
            count += len(x)
            if batch % 100 == 0:
                state['current_batch'] = {
                    'epoch': epoch + 1, 'batch': batch + 1,
                    'batches': len(train_loader), 'train_mse_so_far': float(total) / count,
                }
                update()
        model.eval()
        validation_total = torch.zeros((), device=device) if resident is not None else 0.0
        validation_count = 0
        with torch.no_grad():
            for x, y, _ in validation_loader:
                loss = loss_function(model(x.to(device)), y.to(device))
                if resident is not None:
                    checked_loss(loss)
                elif not torch.isfinite(loss):
                    raise ValueError('Non-finite validation loss')
                validation_total += (loss if resident is not None else float(loss)) * len(x)
                validation_count += len(x)
        validation_loss = float(validation_total) / validation_count
        training_loss = float(total) / count
        state['epochs'].append({
            'epoch': epoch + 1, 'train_mse': training_loss,
            'validation_mse': validation_loss, 'seconds': time.monotonic() - started,
        })
        if validation_loss < best_loss:
            best_loss = validation_loss
            state['best_epoch'] = epoch + 1
            torch.save(base_model.state_dict(), args.output_directory / 'best-model.pt')
        logger.info('Epoch %d/%d train %.6f validation %.6f',
                    epoch + 1, args.epochs, training_loss, validation_loss)
        update()
    base_model.load_state_dict(torch.load(args.output_directory / 'best-model.pt',
                                         map_location=device, weights_only=True))
    model.eval()
    state['status'] = 'validation_threshold_selection'
    update()

    def predict(indices):
        records = []
        with torch.no_grad():
            for x, _, sample_indices in loader(indices):
                output = model(x.to(device)).cpu().numpy()
                output = output * panel['target_scale'] + panel['target_mean']
                if not np.isfinite(output).all():
                    raise ValueError('Non-finite predictions')
                for sample, value in zip(sample_indices.tolist(), output.tolist()):
                    symbol, origin, target, split = panel['metadata'][sample]
                    records.append({
                        'symbol': symbol, 'origin': origin, 'target': target,
                        'partition': split, 'prediction': value,
                        'actual': (float(panel['y'][sample])
                                   if np.isfinite(panel['y'][sample]) else None),
                    })
        return records

    def prediction_map(records):
        mapping = {}
        for row in records:
            mapping.setdefault(row['origin'], {})[row['symbol']] = row['prediction']
        return mapping

    # Signals must predate the next-open fill. Boundary-crossing predictions
    # are available for trading, but their labels never enter model fitting.
    first_validation_session = next(day for day in sessions if day >= config.validation_start)
    validation_signal_start = sessions[sessions.index(first_validation_session) - 1]
    validation_indices = np.asarray([
        index for index, row in enumerate(panel['metadata'])
        if validation_signal_start <= row[1] < config.test_start
    ])
    validation_records = predict(validation_indices)
    validation_predictions = prediction_map(validation_records)
    validation_end = max(day for day in sessions if day < config.test_start)
    candidates = []
    for threshold in (0.0, 0.005, 0.01, 0.02):
        result = simulate_rotation(
            prices, validation_predictions, sessions, config.validation_start,
            validation_end, config, threshold,
        )
        candidates.append({'threshold': threshold, 'total_return': result['total_return']})
    chosen = max(candidates, key=lambda row: (row['total_return'], row['threshold']))['threshold']
    state['threshold_selection'] = {'partition': 'validation', 'candidates': candidates,
                                    'selected': chosen}

    def finance_progress(name):
        def publish(curve):
            state[name] = {'curve': list(curve)}
            update()
        return publish

    state['validation'] = simulate_rotation(
        prices, validation_predictions, sessions, config.validation_start, validation_end,
        config, chosen, finance_progress('validation'),
    )
    labeled_validation = [row for row in validation_records if row['partition'] == 'validation']
    state['validation_metrics'] = evaluate_return_predictions(
        [r['actual'] for r in labeled_validation],
        [r['prediction'] for r in labeled_validation],
    )
    state['status'] = 'held_out_test'
    update()
    first_test_session = next(day for day in sessions if day >= config.test_start)
    test_signal_start = sessions[sessions.index(first_test_session) - 1]
    test_records = predict(np.asarray([
        index for index, row in enumerate(panel['metadata']) if row[1] >= test_signal_start
    ]))
    state['test'] = simulate_rotation(
        prices, prediction_map(test_records), sessions, config.test_start,
        provenance['effective_end'], config, chosen, finance_progress('test'),
    )
    labeled_test = [row for row in test_records if row['partition'] == 'test']
    state['test_metrics'] = evaluate_return_predictions(
        [r['actual'] for r in labeled_test], [r['prediction'] for r in labeled_test],
    )
    pd.DataFrame(validation_records + test_records).to_csv(
        args.output_directory / 'predictions.csv', index=False,
    )
    state['financial_metrics'] = {
        name: {key: state[name][key] for key in
               ('total_return', 'max_drawdown', 'sharpe_zero_rate', 'fees')}
        for name in ('validation', 'test')
    }
    state['status'] = 'completed'
    update()
    save_json(args.output_directory / 'results.json', state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=STOCKS_DATABASE_PATH)
    parser.add_argument('--output-directory', type=Path, required=True)
    parser.add_argument('--epochs', type=int, default=20)
    parser.add_argument('--batch-size', type=int, default=512)
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--device', default='auto',
                        help='auto, cpu or cuda:N; explicit CUDA never falls back to CPU')
    parser.add_argument('--gpu-ids', type=int, nargs='+',
                        help='Train one shared model on multiple GPUs, e.g. --gpu-ids 0 1')
    parser.add_argument('--batch-backend', choices=('auto', 'legacy', 'resident'), default='auto',
                        help='auto uses compact GPU-resident batching on CUDA, legacy on CPU')
    parser.add_argument('--symbol-limit', type=int, default=0,
                        help='Nonzero means smoke subset, NOT full-market performance')
    args = parser.parse_args()
    if min(args.epochs, args.batch_size, args.threads) < 1 or args.symbol_limit < 0:
        parser.error('Epochs, batch size and threads must be positive; symbol limit >= 0')
    if not args.database.is_file():
        parser.error(f'Database not found: {args.database}')
    args.output_directory.mkdir(parents=True, exist_ok=False)
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
        handlers=[logging.FileHandler(args.output_directory / 'run.log', encoding='utf-8'),
                  logging.StreamHandler()],
    )
    state = {'status': 'starting', 'epochs': [], 'limitations': LIMITATIONS,
             'requested_epochs': args.epochs}

    def update():
        state['updated_at'] = datetime.now().astimezone().isoformat()
        report(args.output_directory, state)

    update()
    try:
        run(args, state, update)
    except (OSError, ValueError, RuntimeError, ImportError, sqlite3.Error):
        logger.exception('Shared-model research stopped')
        state['status'] = 'failed'
        import traceback
        state['error'] = traceback.format_exc()
        update()
        raise


if __name__ == '__main__':
    main()
