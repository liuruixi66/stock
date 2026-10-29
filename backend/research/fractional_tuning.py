"""Bounded pre-test LSTM search with durable studies and validation checkpoints."""

from dataclasses import asdict, dataclass
from datetime import date
import hashlib
import json
import logging
import os
from pathlib import Path

import numpy as np

from market_data.price_basis import PRICE_COLUMNS, frame_digest, research_price_contract
from research.database_fractional import load_fractional_database
from research.fractional_forecast import DifferencingError, ForecastConfig, estimate_order
from research.fractional_lstm import (
    EarlyStopping, LSTMTrial, atomic_replace, build_network, evaluate_return_predictions, fit_trial,
    load_training_checkpoint, prepare_sequences, reconstructed_returns, return_context,
    save_training_checkpoint, training_device,
)

logger = logging.getLogger(__name__)
SEARCH_VERSION = 2
METHODS = ('de_prado', 'log_return')


@dataclass(frozen=True)
class SearchSettings:
    stock_count: int = 6
    total_trials: int = 20
    fold_years: tuple[int, ...] = (2012, 2013, 2014)
    train_start: date = date(2006, 10, 16)
    seed: int = 42
    patience: int = 15
    min_delta: float = 1e-6
    max_epochs: int = 120

    def validate(self, test_start: date) -> None:
        for value in (self.stock_count, self.total_trials, self.max_epochs):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise DifferencingError('Search sizes and epochs must be positive integers')
        if self.total_trials < 8 or self.total_trials % 2:
            raise DifferencingError('Search requires an even total budget >= 8 for both methods')
        if self.max_epochs > 120:
            raise DifferencingError('The bounded initial search supports at most 120 epochs')
        if (len(self.fold_years) < 2 or tuple(sorted(set(self.fold_years))) != self.fold_years
                or any(not isinstance(y, int) or isinstance(y, bool) for y in self.fold_years)):
            raise DifferencingError('Search fold years must be strictly increasing integers')
        if (self.train_start >= date(self.fold_years[0], 1, 1)
                or date(self.fold_years[-1] + 1, 1, 1) > min(test_start, date(2016, 1, 1))):
            raise DifferencingError('All search folds must end before test and before 2016')
        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise DifferencingError('Search seed must be a nonnegative integer')
        EarlyStopping(self.patience, self.min_delta)


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(payload, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    atomic_replace(temporary, path)


def relative_mae(actual, predicted) -> float:
    baseline = float(np.mean(np.abs(actual)))
    if not np.isfinite(baseline) or baseline <= 0:
        raise DifferencingError('Zero-return baseline MAE must be finite and positive')
    return evaluate_return_predictions(actual, predicted)['mae'] / baseline


def prepare_fold(frame, config: ForecastConfig, method: str) -> dict:
    """Only the training slice determines differencing and preprocessing."""
    frame = frame[
        (frame['date'] >= config.train_start) & (frame['date'] < config.test_start)
    ].copy()
    training = frame[frame['date'] < config.validation_start]
    if method == 'de_prado':
        order_details = estimate_order(np.log(training['close'].to_numpy()), config)
    elif method == 'log_return':
        order_details = {'order': 1.0, 'estimation': 'fixed_first_difference'}
    else:
        raise DifferencingError(f'Unsupported method: {method}')
    data = prepare_sequences(frame, config, order_details['order'])
    train_indices = np.flatnonzero(data['train'])
    validation_indices = np.flatnonzero(data['validation'])
    context = return_context(data, validation_indices, data['y_mean'], data['y_scale'])
    train_context = return_context(data, train_indices, data['y_mean'], data['y_scale'])
    signs, counts = np.unique(np.sign(train_context['actual']), return_counts=True)
    majority = float(signs[np.argmax(counts)])
    return {
        'data': data, 'train_indices': train_indices,
        'validation_indices': validation_indices, 'context': context,
        'metadata': {
            'instrument': str(frame['instrument'].iloc[0]), 'method': method,
            'train_start': config.train_start.isoformat(),
            'validation_start': config.validation_start.isoformat(),
            'validation_end_exclusive': config.test_start.isoformat(),
            'training_last_target': data['target_dates'][train_indices[-1]].isoformat(),
            'train_samples': int(len(train_indices)),
            'validation_samples': int(len(validation_indices)),
            'order_details': order_details,
            'scaler': {
                'x_mean': data['x_mean'].tolist(), 'x_scale': data['x_scale'].tolist(),
                'y_mean': data['y_mean'], 'y_scale': data['y_scale'],
            },
            'weights': data['weights'].tolist(),
            'feature_count': int(data['x'].shape[-1]),
            'sequence_length': config.sequence_length,
            'config': {k: v.isoformat() if isinstance(v, date) else v
                       for k, v in asdict(config).items()},
            'selected_prices_sha256': frame_digest(frame, PRICE_COLUMNS),
            'majority_direction': majority,
        },
    }


def _candidate(optuna_trial, settings: SearchSettings) -> LSTMTrial:
    layers = optuna_trial.suggest_categorical('num_layers', [1, 2])
    return LSTMTrial(
        hidden_size=optuna_trial.suggest_categorical('hidden_size', [16, 32, 64]),
        learning_rate=optuna_trial.suggest_float('learning_rate', 0.0003, 0.003, log=True),
        batch_size=optuna_trial.suggest_categorical('batch_size', [32, 64, 128]),
        num_layers=layers,
        dropout=optuna_trial.suggest_categorical('dropout', [0.0, 0.1, 0.2]) if layers > 1 else 0.0,
        epochs=optuna_trial.suggest_categorical(
            'epochs', sorted({min(n, settings.max_epochs) for n in (30, 60, 90, 120)}),
        ),
    )


def _enqueue_baselines(study, settings: SearchSettings) -> None:
    for hidden, layers, epochs in ((16, 1, 30), (32, 1, 30), (64, 1, 90), (32, 2, 90)):
        study.enqueue_trial({
            'num_layers': layers, 'hidden_size': hidden, 'learning_rate': 0.001,
            'batch_size': 64, 'dropout': 0.1,
            'epochs': min(epochs, settings.max_epochs),
        })


def _trial_record(trial) -> dict:
    return {
        'number': trial.number, 'state': trial.state.name, 'value': trial.value,
        'parameters': trial.params, 'diagnostics': trial.user_attrs,
    }


def _search_method(study, prepared: list[dict], settings: SearchSettings, root: Path) -> dict:
    import optuna
    import torch

    device = training_device()
    limit = settings.total_trials // len(METHODS)
    for old in study.get_trials(deepcopy=False):
        if old.state == optuna.trial.TrialState.RUNNING:
            interrupted = study.user_attrs.get('interrupted_trials', [])
            study.set_user_attr('interrupted_trials', [*interrupted, old.number])
            study.tell(old.number, state=optuna.trial.TrialState.FAIL)
    if not study.trials:
        _enqueue_baselines(study, settings)
    attempted = sum(t.state != optuna.trial.TrialState.WAITING for t in study.trials)
    while attempted < limit:
        # A per-trial sampler seed makes restart behavior independent of lost RNG state.
        study.sampler = optuna.samplers.TPESampler(
            seed=settings.seed + len(study.trials), n_startup_trials=4,
        )
        trial = study.ask()
        candidate = _candidate(trial, settings)
        trial.set_user_attr('trial_config', asdict(candidate))
        rows, scores = [], []
        try:
            for fold_index, fold in enumerate(prepared):
                data, metadata = fold['data'], fold['metadata']
                path = root / f'trial-{trial.number:03d}' / f'fold-{fold_index:02d}.pt'
                context = fold['context']

                def save_best(best):
                    save_training_checkpoint(path, {
                        **metadata, **best, 'trial': asdict(candidate),
                        'kind': 'validation_selection', 'seed': settings.seed,
                        'selection_metric': 'return_mae',
                        'early_stopping_patience': settings.patience,
                        'min_delta': settings.min_delta,
                        'study_signature': study.user_attrs['signature'],
                    })

                result = fit_trial(
                    torch.from_numpy(data['x']).to(device),
                    torch.from_numpy(data['y']).to(device),
                    torch.from_numpy(fold['train_indices']).to(device),
                    torch.from_numpy(fold['validation_indices']).to(device),
                    candidate, seed=settings.seed, patience=settings.patience,
                    min_delta=settings.min_delta, context=context,
                    on_improvement=save_best,
                )
                model = build_network(metadata['feature_count'], candidate).to(device)
                model.load_state_dict(result['model'])
                model.eval()
                with torch.no_grad():
                    outputs = model(torch.from_numpy(
                        data['x'][fold['validation_indices']],
                    ).to(device)).cpu().numpy()
                predicted = reconstructed_returns(outputs, context)
                actual = context['actual']
                score = relative_mae(actual, predicted)
                scores.append(score)
                rows.append({
                    **metadata, 'checkpoint': str(path.resolve()),
                    'epoch': result['epoch'], 'stopped_early': result['stopped_early'],
                    'epochs_run': len(result['epoch_history']),
                    'epoch_history': result['epoch_history'],
                    'metrics': evaluate_return_predictions(actual, predicted),
                    'zero_return_baseline': evaluate_return_predictions(actual, np.zeros_like(actual)),
                    'relative_mae': score, 'zero_return_skill': 1 - score,
                    'majority_direction_accuracy_percent': float(
                        np.mean(np.sign(actual) == metadata['majority_direction']) * 100,
                    ),
                })
                trial.set_user_attr('folds', rows)
                trial.report(float(np.mean(scores)), fold_index)
                if trial.should_prune():
                    raise optuna.TrialPruned()
            study.tell(trial, float(np.mean(scores)))
        except optuna.TrialPruned:
            study.tell(trial, state=optuna.trial.TrialState.PRUNED)
        except (DifferencingError, RuntimeError, OSError, KeyboardInterrupt) as exc:
            trial.set_user_attr('error', f'{type(exc).__name__}: {exc}')
            study.tell(trial, state=optuna.trial.TrialState.FAIL)
            logger.exception('Search trial %s failed; study is preserved', trial.number)
            raise
        attempted += 1
        logger.info('%s: attempted %d/%d; trial %d is %s', study.study_name,
                    attempted, limit, trial.number, study.trials[trial.number].state.name)
    complete = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    if not complete:
        raise DifferencingError(f'No completed search trials in {study.study_name}')
    best = min(complete, key=lambda t: t.value)
    return {
        'best_trial_number': best.number, 'relative_mae': best.value,
        'zero_return_skill': 1 - best.value, 'qualified_vs_zero_baseline': best.value < 1,
        'selected_trial': best.user_attrs['trial_config'],
        'best_folds': best.user_attrs['folds'],
        'trials': [_trial_record(t) for t in study.trials],
        'interrupted_trials': study.user_attrs.get('interrupted_trials', []),
        'training_device': str(device), 'torch_version': str(torch.__version__),
        'gpu_name': torch.cuda.get_device_name(device) if device.type == 'cuda' else None,
    }


def run_search(
    database: Path, directory: Path, settings: SearchSettings | None = None, *,
    test_start: date = date(2016, 10, 14), resume: bool = False,
) -> dict:
    """Search only pre-test folds; never silently load an incompatible study."""
    import optuna

    settings = settings or SearchSettings()
    settings.validate(test_start)
    database, directory = Path(database).resolve(), Path(directory).resolve()
    if directory.exists() and not resume:
        raise DifferencingError(f'Search directory exists; use explicit --resume: {directory}')
    if resume and not (directory / 'manifest.json').exists():
        raise DifferencingError('Search resume requires an existing manifest')
    directory.mkdir(parents=True, exist_ok=True)
    cutoff = date(settings.fold_years[-1] + 1, 1, 1)
    config = ForecastConfig(
        train_start=settings.train_start,
        validation_start=date(settings.fold_years[0], 1, 1),
        test_start=date(settings.fold_years[-1], 1, 1),
        test_end=date(cutoff.year - 1, 12, 31),
    )
    prices, _, provenance = load_fractional_database(
        database, config, seed=settings.seed, universe_size=settings.stock_count,
    )
    parameters = asdict(settings)
    parameters['train_start'] = settings.train_start.isoformat()
    parameters['fold_years'] = list(settings.fold_years)
    stat = database.stat()
    manifest = {
        'search_version': SEARCH_VERSION, 'parameters': parameters,
        'database': str(database), 'database_size': stat.st_size,
        'database_mtime_ns': stat.st_mtime_ns, 'data_provenance': provenance,
        'test_start': test_start.isoformat(), 'price_contract': research_price_contract(),
        'objective': 'mean_fold_stock_return_mae_divided_by_zero_return_mae',
    }
    # Selection timestamp is descriptive, not an input to numerical reproducibility.
    signed_manifest = {**manifest, 'data_provenance': {
        k: v for k, v in provenance.items() if k != 'universe_selection_date'
    }}
    signature = hashlib.sha256(json.dumps(
        signed_manifest, sort_keys=True, separators=(',', ':'),
    ).encode('utf-8')).hexdigest()
    manifest['signature'] = signature
    manifest_path = directory / 'manifest.json'
    if resume:
        old = json.loads(manifest_path.read_text(encoding='utf-8'))
        if old.get('signature') != signature:
            raise DifferencingError('Search signature/data/configuration changed; use a new directory')
    else:
        atomic_json(manifest_path, manifest)
    storage = optuna.storages.RDBStorage(
        url='sqlite:///' + (directory / 'study.sqlite3').as_posix(),
        engine_kwargs={'connect_args': {'timeout': 60}},
    )
    report = {
        **manifest, 'methods': {}, 'live_trading_eligible': False,
        'limitations': [
            'Historical validation selection is not an untouched test or live performance.',
            'Complete-history stock sampling has survivorship bias.',
            'One initialization seed; robustness across initializations is unverified.',
            'Best epoch is selected and scored on validation; metrics are selection-biased.',
            'Pruned trials do not have complete fold coverage.',
        ],
    }
    try:
        for method in METHODS:
            prepared = []
            for year in settings.fold_years:
                fold_config = ForecastConfig(
                    train_start=settings.train_start, validation_start=date(year, 1, 1),
                    test_start=date(year + 1, 1, 1), test_end=cutoff,
                )
                for _, stock in prices.groupby('instrument', sort=True):
                    prepared.append(prepare_fold(stock, fold_config, method))
            study = optuna.create_study(
                study_name=method, storage=storage, direction='minimize', load_if_exists=resume,
                sampler=optuna.samplers.TPESampler(seed=settings.seed, n_startup_trials=4),
                pruner=optuna.pruners.MedianPruner(
                    n_startup_trials=4, n_warmup_steps=settings.stock_count,
                ),
            )
            if study.user_attrs and study.user_attrs.get('signature') != signature:
                raise DifferencingError('Optuna study signature mismatch')
            study.set_user_attr('signature', signature)
            report['methods'][method] = _search_method(
                study, prepared, settings, directory / method,
            )
            atomic_json(directory / 'report.json', report)
        verify_search_artifacts(directory, report)
        report['verification'] = 'winning_checkpoints_reloaded'
        atomic_json(directory / 'report.json', report)
    finally:
        storage.remove_session()
        storage.engine.dispose()
    return report


def verify_search_artifacts(directory: Path, report: dict) -> None:
    """Reopen winning checkpoints and validate coverage, signature and finite scores."""
    for method in METHODS:
        result = report['methods'][method]
        if not np.isfinite(result['relative_mae']):
            raise DifferencingError('Non-finite winning search objective')
        expected = report['parameters']['stock_count'] * len(report['parameters']['fold_years'])
        if len(result['best_folds']) != expected:
            raise DifferencingError('Winning trial lacks complete validation coverage')
        for fold in result['best_folds']:
            path = Path(fold['checkpoint']).resolve()
            if directory.resolve() not in path.parents:
                raise DifferencingError('Checkpoint is outside experiment directory')
            payload, _ = load_training_checkpoint(path)
            if (payload['study_signature'] != report['signature']
                    or payload['trial'] != result['selected_trial']
                    or payload['epoch'] != fold['epoch']):
                raise DifferencingError('Winning checkpoint does not match search report')
