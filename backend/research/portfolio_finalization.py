"""Refit the selected portfolio model and re-evaluate the viewed historical period."""

from __future__ import annotations

from datetime import date
import json
import logging
from pathlib import Path
from statistics import median
from typing import Mapping

import numpy as np
import torch

from market_data.industry_universe import verify_industry_universe
from market_data.portfolio_history import (
    load_portfolio_history, portfolio_price_contract,
)
from research.portfolio_lstm import (
    FEATURE_NAMES, PortfolioModelConfig, SharedPortfolioLSTM,
    load_model_bundle, save_model_bundle,
    train_shared_model, unwrap_shared_model, wrap_model_for_training,
)
from research.portfolio_tuning import (
    UNEXPLAINED_GAP_EXCLUSIONS, PortfolioSearchSettings,
    _fit_symbol_weights, _training_batches, score_panel, simulate_portfolio,
    build_portfolio_panel,
)
from research.fractional_lstm import training_device


logger = logging.getLogger(__name__)
HISTORICAL_REEVALUATION_START = date(2016, 10, 14)
HISTORICAL_REEVALUATION_END = date(2026, 10, 14)
HISTORY_DATA_END = date(2026, 10, 30)


def _selected_trial_report(search_report: Mapping) -> dict:
    if search_report.get('search_qualified') is not True:
        raise ValueError('Search report has no drawdown-qualified method')
    method = search_report.get('selected_method')
    trial_number = search_report.get('selected_trial')
    if method not in ('de_prado', 'log_return') or not isinstance(trial_number, int):
        raise ValueError('Search report has an invalid selected model identity')
    candidates = search_report['methods'][method]['trials']
    selected = [trial for trial in candidates if trial['number'] == trial_number]
    if len(selected) != 1 or selected[0]['diagnostics'].get('qualified') is not True:
        raise ValueError('Selected trial is missing or not qualified')
    return selected[0]


def finalize_portfolio_search(
    database: Path,
    universe_path: Path,
    audit_path: Path,
    search_report_path: Path,
    output_directory: Path,
) -> dict:
    database, universe_path, audit_path, search_report_path, output_directory = (
        Path(database).resolve(), Path(universe_path).resolve(), Path(audit_path).resolve(),
        Path(search_report_path).resolve(), Path(output_directory).resolve(),
    )
    if output_directory.exists() and any(
        entry.name != 'run.json' for entry in output_directory.iterdir()
    ):
        raise ValueError(f'Final training output already exists: {output_directory}')
    with universe_path.open('r', encoding='utf-8') as stream:
        universe = json.load(stream)
    with audit_path.open('r', encoding='utf-8') as stream:
        audit = json.load(stream)
    with search_report_path.open('r', encoding='utf-8') as stream:
        search_report = json.load(stream)
    verify_industry_universe(universe)
    if (audit.get('status') != 'passed'
            or audit.get('universe_signature') != universe['signature']
            or search_report.get('universe_signature') != universe['signature']
            or search_report.get('search_version') != 1):
        raise ValueError('Finalization requires a passing audit and matching frozen universe')
    if UNEXPLAINED_GAP_EXCLUSIONS & set(universe['selected_instruments']):
        raise ValueError('Final universe contains an unexplained-gap instrument')
    if len(universe['selected_instruments']) != 546:
        raise ValueError('Finalization requires the approved 546-stock child universe')
    selected = _selected_trial_report(search_report)
    method = search_report['selected_method']
    selected_trial = search_report['selected_trial']
    settings = PortfolioSearchSettings()
    parameters = selected['parameters']
    diagnostics = selected['diagnostics']
    epochs = [
        int(diagnostics[f'fold_{year}']['checkpoint_epoch'])
        for year in settings.fold_years
    ]
    final_epochs = max(1, int(median(epochs)))
    config = PortfolioModelConfig(
        hidden_size=int(parameters['hidden_size']),
        num_layers=int(parameters['num_layers']),
        dropout=float(parameters.get('dropout', 0.0)),
        batch_size=int(parameters['batch_size']),
        learning_rate=float(parameters['learning_rate']),
        sequence_length=settings.sequence_length,
        maximum_positions=settings.positions,
        exposure=settings.exposure,
        buy_cost=settings.buy_cost,
        sell_cost=settings.sell_cost,
        signal_threshold=settings.signal_threshold,
        max_drawdown_limit=settings.max_drawdown,
        max_epochs=final_epochs,
        patience=settings.patience,
        seed=settings.seed,
    )
    history, sessions, suspended_sessions, provenance = load_portfolio_history(
        database, universe, settings.train_start, HISTORY_DATA_END,
    )
    if (provenance['prices_sha256'] != search_report['prices_sha256']
            or provenance['calendar_sha256'] != search_report['calendar_sha256']):
        raise ValueError('Price or calendar digest changed since the selected search')
    weights, excluded = _fit_symbol_weights(
        history, universe['selected_instruments'], method, settings.train_start,
        HISTORICAL_REEVALUATION_START, HISTORICAL_REEVALUATION_END,
    )
    panel = build_portfolio_panel(
        history, sessions, suspended_sessions, universe['selected_instruments'], weights,
        train_start=settings.train_start,
        validation_start=HISTORICAL_REEVALUATION_START,
        sequence_length=settings.sequence_length,
    )
    panel.excluded_symbols.update(excluded)
    training_batches = _training_batches(
        panel, HISTORICAL_REEVALUATION_START, config.batch_size,
    )
    device = training_device()
    model = SharedPortfolioLSTM(len(FEATURE_NAMES), config).to(device)
    model = wrap_model_for_training(model, device)
    fit_record = train_shared_model(model, training_batches, config)
    signal_indices = [
        index for index, day in enumerate(panel.dates[:-1])
        if HISTORICAL_REEVALUATION_START <= day <= HISTORICAL_REEVALUATION_END
        and index >= config.sequence_length - 1
    ]
    if not signal_indices:
        raise ValueError('Historical re-evaluation has no valid signal dates')
    scores = score_panel(model, panel, signal_indices, config.batch_size)
    historical = simulate_portfolio(
        panel, scores, signal_indices, config, settings.initial_capital,
    )
    validation_years = {
        str(year): {
            'return': float(search_report['selected_validation'][str(year)]['return']),
            'max_drawdown': float(
                search_report['selected_validation'][str(year)]['max_drawdown'],
            ),
        }
        for year in settings.fold_years
    }
    bundle_path = output_directory / 'models' / 'selected'
    metadata = {
        'run_id': output_directory.name,
        'parent_search_run_id': search_report.get('run_id'),
        'method': method,
        'trial': selected_trial,
        'epoch': final_epochs,
        'training_status': 'final_refit_historical_re_evaluation',
        'selection_metric': 'validation_mean_return_subject_to_each_year_drawdown_limit',
        'selected_validation': validation_years,
        'validation': {
            'passed': all(
                item['max_drawdown'] <= settings.max_drawdown
                for item in validation_years.values()
            ),
            'max_drawdown_limit': settings.max_drawdown,
            'max_drawdown_by_year': {
                year: item['max_drawdown'] for year, item in validation_years.items()
            },
            'mean_annual_return': float(search_report['methods'][method]['winner'][
                'validation_mean_return'
            ]),
        },
        'training': {
            'start': settings.train_start.isoformat(),
            'end_exclusive': HISTORICAL_REEVALUATION_START.isoformat(),
            'seed': settings.seed,
            'search_max_epochs': settings.max_epochs,
            'refit_epochs': final_epochs,
            'median_selected_fold_epoch': final_epochs,
            'minimum_training_loss': fit_record['minimum_training_loss'],
        },
        'historical_re_evaluation': {
            'start': HISTORICAL_REEVALUATION_START.isoformat(),
            'end': HISTORICAL_REEVALUATION_END.isoformat(),
            'portfolio_return': historical['portfolio_return'],
            'max_drawdown': historical['max_drawdown'],
            'fees': historical['fees'],
            'trade_count': historical['trade_count'],
            'passed_20_percent_drawdown_gate': (
                historical['max_drawdown'] <= settings.max_drawdown
            ),
            'previously_viewed_period_not_an_untouched_test': True,
        },
        'data_provenance': {
            'universe_signature': universe['signature'],
            'prices_sha256': provenance['prices_sha256'],
            'calendar_sha256': provenance['calendar_sha256'],
            'price_contract': portfolio_price_contract(),
            'excluded_method_symbols': panel.excluded_symbols,
        },
    }
    probe_index = signal_indices[0]
    original_probe = score_panel(model, panel, [probe_index], config.batch_size)
    cpu_reference = SharedPortfolioLSTM(len(FEATURE_NAMES), config)
    cpu_reference.load_state_dict({
        name: value.detach().cpu().clone()
        for name, value in unwrap_shared_model(model).state_dict().items()
    })
    cpu_reference.eval()
    cpu_reference_probe = score_panel(
        cpu_reference, panel, [probe_index], config.batch_size,
    )
    bundle_path = save_model_bundle(
        bundle_path, unwrap_shared_model(model), config, sorted(weights), weights,
        panel.scaler, universe['signature'], metadata,
    )
    loaded = load_model_bundle(bundle_path, map_location='cpu')
    reloaded_probe = score_panel(
        loaded.model, panel, [probe_index], config.batch_size,
    )
    max_difference = float(np.max(np.abs(
        cpu_reference_probe[probe_index] - reloaded_probe[probe_index],
    )))
    if not np.allclose(
        cpu_reference_probe[probe_index], reloaded_probe[probe_index],
        rtol=1e-5, atol=1e-6,
    ):
        raise ValueError(
            f'CPU bundle reload scores differ from CPU reference; max abs error={max_difference}',
        )
    cross_device_difference = float(np.max(np.abs(
        original_probe[probe_index] - reloaded_probe[probe_index],
    )))
    if not np.allclose(
        original_probe[probe_index], reloaded_probe[probe_index],
        rtol=1e-4, atol=1e-4,
    ):
        raise ValueError(
            'GPU-to-CPU score adaptation exceeded explicit tolerance; '
            f'max abs error={cross_device_difference}',
        )
    return {
        'finalization_version': 1,
        'parent_search_run_id': search_report['run_id'],
        'universe_signature': universe['signature'],
        'selected_method': method,
        'selected_trial': selected_trial,
        'selected_parameters': parameters,
        'selected_validation': validation_years,
        'final_refit': {
            'start': settings.train_start.isoformat(),
            'end_exclusive': HISTORICAL_REEVALUATION_START.isoformat(),
            'epochs': final_epochs,
            'minimum_training_loss': fit_record['minimum_training_loss'],
            'model_bundle': str(bundle_path),
        },
        'historical_re_evaluation': historical,
        'historical_drawdown_gate_passed': (
            historical['max_drawdown'] <= settings.max_drawdown
        ),
        'bundle_reload': {
            'passed': True, 'map_location': 'cpu',
            'probe_date': panel.dates[probe_index].isoformat(),
            'max_absolute_score_difference': max_difference,
            'rtol': 1e-5, 'atol': 1e-6,
        },
        'cross_device_reload': {
            'passed': True, 'map_location': 'cpu',
            'max_absolute_score_difference': cross_device_difference,
            'rtol': 1e-4, 'atol': 1e-4,
        },
        'live_trading_eligible': False,
        'limitations': [
            'Current industry snapshot retains lookahead and survivorship bias.',
            'Historical ST status is unknown; no live eligibility is claimed.',
            '2016-2026 is a previously viewed historical re-evaluation, not an untouched test.',
            'This continuous adjusted-price simulation does not model lots, T+1, price limits, or market impact.',
        ],
    }
