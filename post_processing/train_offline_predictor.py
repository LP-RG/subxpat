#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np


FEATURE_NAMES = [
    'iteration',
    'out_node',
    'beta',
    'max_error',
    'best_seen_stagnation',
    'best_seen_iteration_age',
    'same_subgraph_streak',
    'structural_stall_streak',
    'negative_ratio',
    'timeout_count',
    'runtime_fraction',
    'best_seen_improvement_pct',
    'bit_weight_over_ceiling',
]


def _as_float(value: object, default: float = 0.0) -> float:
    if value in (None, '', 'None'):
        return default
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    text = str(value).strip()
    if text.lower() in {'true', 'false'}:
        return 1.0 if text.lower() == 'true' else 0.0
    try:
        return float(text)
    except ValueError:
        return default


def _feature_vector(row: Dict[str, str], summary: Dict[str, object]) -> Dict[str, float]:
    runtime_seconds = _as_float(summary.get('runtime_seconds'), 0.0)
    timeout = max(_as_float(summary.get('runtime_seconds'), 0.0), 1.0)
    if _as_float(summary.get('runtime_seconds'), 0.0) <= 0:
        timeout = 1.0
    configured_timeout = _as_float(summary.get('timeout'), 0.0)
    if configured_timeout > 0:
        timeout = configured_timeout
    bit_weight = _as_float(row.get('bit_weight'), 0.0)
    ceiling = _as_float(row.get('termination_ceiling'), 0.0)
    return {
        'iteration': _as_float(row.get('iteration')),
        'out_node': _as_float(row.get('out_node')),
        'beta': _as_float(summary.get('beta')),
        'max_error': _as_float(summary.get('max_error')),
        'best_seen_stagnation': _as_float(row.get('best_seen_stagnation')),
        'best_seen_iteration_age': max(
            0.0,
            _as_float(row.get('iteration')) - _as_float(row.get('run_best_iteration'), _as_float(row.get('iteration'))),
        ),
        'same_subgraph_streak': _as_float(row.get('same_subgraph_streak')),
        'structural_stall_streak': _as_float(row.get('structural_stall_streak')),
        'negative_ratio': _as_float(row.get('grid_negative_ratio')),
        'timeout_count': _as_float(row.get('grid_timeout_count')),
        'runtime_fraction': _as_float(summary.get('runtime_seconds')) / timeout if timeout > 0 else 0.0,
        'best_seen_improvement_pct': _as_float(row.get('best_seen_improvement_pct')),
        'bit_weight_over_ceiling': bit_weight / max(ceiling, 1e-9) if ceiling > 0 else 0.0,
    }


def _load_samples(trace_root: Path, tolerance_pct: float, benchmark_filter: str) -> Tuple[np.ndarray, np.ndarray]:
    samples: List[List[float]] = []
    labels: List[float] = []

    for trace_path in sorted(trace_root.rglob('grid_*_trace.csv')):
        summary_path = trace_path.with_name(trace_path.name.replace('_trace.csv', '_summary.json'))
        if not summary_path.exists():
            continue
        summary = json.load(open(summary_path))
        benchmark = str(summary.get('exact_benchmark') or summary.get('final_benchmark') or '')
        if benchmark_filter and benchmark != benchmark_filter:
            continue
        if str(summary.get('cnn_constraint')) != 'zone_aet':
            continue

        with open(trace_path) as trace_file:
            rows = list(csv.DictReader(trace_file))

        final_best_area = _as_float(summary.get('best_seen_area'), 0.0)
        if final_best_area <= 0:
            final_best_area = _as_float(summary.get('final_area'), 0.0)
        if final_best_area <= 0 and rows:
            candidates = [
                _as_float(row.get('run_best_area', row.get('best_area')), 0.0)
                for row in rows
            ]
            candidates = [value for value in candidates if value > 0]
            if candidates:
                final_best_area = min(candidates)
        if final_best_area <= 0:
            continue

        for row in rows:
            status = str(row.get('status') or '')
            if status == 'STOPPED':
                continue
            current_best = _as_float(
                row.get('run_best_area', row.get('best_area')),
                0.0,
            )
            if current_best <= 0:
                continue
            future_improvement_pct = max(0.0, ((current_best - final_best_area) / current_best) * 100.0)
            label = 1.0 if future_improvement_pct <= tolerance_pct else 0.0
            feature_map = _feature_vector(row, summary)
            samples.append([feature_map[name] for name in FEATURE_NAMES])
            labels.append(label)

    if not samples:
        raise SystemExit('No training samples found for offline predictor.')
    return np.asarray(samples, dtype=float), np.asarray(labels, dtype=float)


def _fit_logistic_regression(X: np.ndarray, y: np.ndarray, *, seed: int, epochs: int = 2500, lr: float = 0.05, l2: float = 1e-3) -> Tuple[np.ndarray, float, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    means = X.mean(axis=0)
    stds = X.std(axis=0)
    stds = np.where(stds < 1e-9, 1.0, stds)
    Xn = (X - means) / stds
    weights = rng.normal(0.0, 0.05, size=Xn.shape[1])
    bias = 0.0

    for _ in range(epochs):
        logits = Xn @ weights + bias
        logits = np.clip(logits, -60.0, 60.0)
        probs = 1.0 / (1.0 + np.exp(-logits))
        error = probs - y
        grad_w = (Xn.T @ error) / len(Xn) + l2 * weights
        grad_b = float(error.mean())
        weights -= lr * grad_w
        bias -= lr * grad_b

    return weights, float(bias), means, stds


def _evaluate(X: np.ndarray, y: np.ndarray, weights: np.ndarray, bias: float, means: np.ndarray, stds: np.ndarray, threshold: float) -> Dict[str, float]:
    Xn = (X - means) / stds
    logits = np.clip(Xn @ weights + bias, -60.0, 60.0)
    probs = 1.0 / (1.0 + np.exp(-logits))
    preds = (probs >= threshold).astype(float)
    accuracy = float((preds == y).mean())
    true_pos = float(((preds == 1) & (y == 1)).sum())
    false_pos = float(((preds == 1) & (y == 0)).sum())
    false_neg = float(((preds == 0) & (y == 1)).sum())
    precision = true_pos / max(true_pos + false_pos, 1.0)
    recall = true_pos / max(true_pos + false_neg, 1.0)
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'positive_rate': float(preds.mean()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description='Train an offline learned termination predictor from SubXPAT traces.')
    parser.add_argument('--trace-root', type=Path, default=Path('output/report/termination_study'))
    parser.add_argument('--output-model', type=Path, required=True)
    parser.add_argument('--benchmark', type=str, default='mul_i10_o10')
    parser.add_argument('--tolerance-pct', type=float, default=1.0)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--prob-threshold', type=float, default=0.80)
    args = parser.parse_args()

    X, y = _load_samples(args.trace_root, args.tolerance_pct, args.benchmark)
    indices = list(range(len(X)))
    random.Random(args.seed).shuffle(indices)
    split = max(1, int(0.8 * len(indices)))
    train_idx = indices[:split]
    val_idx = indices[split:] or indices[:split]

    weights, bias, means, stds = _fit_logistic_regression(X[train_idx], y[train_idx], seed=args.seed)
    train_metrics = _evaluate(X[train_idx], y[train_idx], weights, bias, means, stds, args.prob_threshold)
    val_metrics = _evaluate(X[val_idx], y[val_idx], weights, bias, means, stds, args.prob_threshold)

    model = {
        'model_type': 'logistic_regression',
        'benchmark': args.benchmark,
        'feature_names': FEATURE_NAMES,
        'feature_means': means.tolist(),
        'feature_stds': stds.tolist(),
        'weights': weights.tolist(),
        'bias': bias,
        'label_tolerance_pct': args.tolerance_pct,
        'probability_threshold': args.prob_threshold,
        'sample_count': int(len(X)),
        'train_count': int(len(train_idx)),
        'validation_count': int(len(val_idx)),
        'train_metrics': train_metrics,
        'validation_metrics': val_metrics,
    }

    args.output_model.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_model, 'w') as model_file:
        json.dump(model, model_file, indent=2, sort_keys=True)

    print(json.dumps({
        'output_model': str(args.output_model),
        'sample_count': len(X),
        'train_metrics': train_metrics,
        'validation_metrics': val_metrics,
    }, indent=2))


if __name__ == '__main__':
    main()
