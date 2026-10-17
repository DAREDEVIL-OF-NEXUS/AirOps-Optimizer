"""Chronological Train/Test Split Generator and Ground-Truth Target Synthesis.

This module provides reproducible, strictly chronological dataset partitioning:
1. No future-to-past data leakage: Train split [0, t_split], Test split (t_split, t_max].
2. Synthetic ground-truth labeling functions based on physics-informed degradation
   and operational queuing dynamics.
3. Formats feature matrices and labels for downstream LightGBM / scikit-learn models.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.prediction.features import PredictiveFeaturePipeline


@dataclass(frozen=True)
class ChronologicalDataset:
    """Container for chronologically split training and evaluation data."""

    X_train: np.ndarray
    y_train: np.ndarray
    X_val: np.ndarray
    y_val: np.ndarray
    feature_names: list[str]
    split_minute: float


class ChronologicalSplitGenerator:
    """Generates chronologically ordered dataset splits and synthetic labels."""

    @classmethod
    def generate_synthetic_training_corpus(
        cls,
        num_aircraft: int = 50,
        num_days: int = 30,
        split_ratio: float = 0.8,
        random_seed: int = 42,
    ) -> tuple[ChronologicalDataset, ChronologicalDataset]:
        """Generate synthetic state history and return (failure_dataset, delay_dataset)."""
        rng = np.random.default_rng(random_seed)

        # 1. Generate Aircraft Failure Corpus
        total_samples = num_aircraft * num_days
        split_point = int(total_samples * split_ratio)

        # Features: [hours, cycles, since_maint, is_fast_jet, is_heavy, is_rotary, upcoming_tasks, congestion]
        hours = rng.uniform(50.0, 3000.0, size=total_samples)
        cycles = hours * rng.uniform(0.3, 0.8, size=total_samples)
        since_maint = rng.exponential(scale=300.0, size=total_samples)
        ac_types = rng.integers(0, 3, size=total_samples)
        is_fast_jet = (ac_types == 0).astype(float)
        is_heavy = (ac_types == 1).astype(float)
        is_rotary = (ac_types == 2).astype(float)
        upcoming_tasks = rng.poisson(lam=4, size=total_samples).astype(float)
        congestion = upcoming_tasks / max(1.0, float(num_aircraft))

        X_ac = np.column_stack([
            hours,
            cycles,
            since_maint,
            is_fast_jet,
            is_heavy,
            is_rotary,
            upcoming_tasks,
            congestion,
        ]).astype(np.float32)

        # Ground truth failure risk probability (physics-informed logistic response)
        # Risk increases with high hours, high cycles, long time since maintenance, and fast jets
        logits = (
            -4.5
            + 0.0008 * hours
            + 0.0015 * cycles
            + 0.003 * since_maint
            + 0.6 * is_fast_jet
            + 0.2 * congestion
            + rng.normal(0.0, 0.3, size=total_samples)
        )
        p_failure = 1.0 / (1.0 + np.exp(-logits))
        y_failure = (rng.uniform(0.0, 1.0, size=total_samples) < p_failure).astype(int)

        dataset_failure = ChronologicalDataset(
            X_train=X_ac[:split_point],
            y_train=y_failure[:split_point],
            X_val=X_ac[split_point:],
            y_val=y_failure[split_point:],
            feature_names=PredictiveFeaturePipeline.FEATURE_NAMES_AIRCRAFT,
            split_minute=float(split_point),
        )

        # 2. Generate Task Turnaround Delay Corpus
        # Features: [duration, priority, est, flexibility, is_cap, is_transport, is_recon, origin_traffic]
        num_tasks = total_samples * 2
        split_task = int(num_tasks * split_ratio)

        duration = rng.uniform(30.0, 240.0, size=num_tasks)
        priority = rng.uniform(1.0, 5.0, size=num_tasks)
        est = rng.uniform(0.0, 1440.0, size=num_tasks)
        flexibility = rng.uniform(0.0, 180.0, size=num_tasks)
        task_types = rng.integers(0, 3, size=num_tasks)
        is_cap = (task_types == 0).astype(float)
        is_transport = (task_types == 1).astype(float)
        is_recon = (task_types == 2).astype(float)
        origin_traffic = 1.0 + (duration / 60.0) + rng.uniform(0.0, 3.0, size=num_tasks)

        X_task = np.column_stack([
            duration,
            priority,
            est,
            flexibility,
            is_cap,
            is_transport,
            is_recon,
            origin_traffic,
        ]).astype(np.float32)

        # Expected turnaround delay (minutes)
        expected_delay = (
            5.0
            + 0.1 * duration
            + 3.0 * origin_traffic
            - 0.02 * flexibility
            + rng.normal(0.0, 4.0, size=num_tasks)
        )
        y_delay = np.clip(expected_delay, 0.0, 120.0).astype(np.float32)

        dataset_delay = ChronologicalDataset(
            X_train=X_task[:split_task],
            y_train=y_delay[:split_task],
            X_val=X_task[split_task:],
            y_val=y_delay[split_task:],
            feature_names=PredictiveFeaturePipeline.FEATURE_NAMES_TASK,
            split_minute=float(split_task),
        )

        return dataset_failure, dataset_delay
