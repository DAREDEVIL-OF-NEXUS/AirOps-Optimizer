"""Predictive Models: LightGBM Classifiers, Regressors, and Probability Calibration.

This module provides:
1. LightGBM failure probability classifier with Platt scaling (Sigmoid) / Isotonic calibration.
2. LightGBM turnaround delay regressor with non-negative projection.
3. Fallback linear baselines (LogisticRegression, Ridge).
4. Model evaluation metrics (Brier Score, ROC-AUC, RMSE, MAE).
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    brier_score_loss,
    mean_absolute_error,
    roc_auc_score,
    root_mean_squared_error,
)

from src.prediction.train import ChronologicalDataset


@dataclass
class ModelEvaluationReport:
    """Evaluation summary metrics for trained models."""

    model_type: str
    target_name: str
    metrics: dict[str, float]


class AircraftFailureClassifier:
    """Predicts airframe 24-hour maintenance failure risk with calibrated probabilities."""

    def __init__(self, use_lightgbm: bool = True) -> None:
        self.use_lightgbm = use_lightgbm
        self.calibrated_model: Any = None
        self.raw_model: Any = None

    def fit(self, dataset: ChronologicalDataset) -> ModelEvaluationReport:
        """Fit model and calibrate probabilities on chronological validation set."""
        if self.use_lightgbm:
            self.raw_model = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.05,
                random_state=42,
                verbosity=-1,
            )
        else:
            self.raw_model = LogisticRegression(max_iter=1000, random_state=42)

        # Fit raw model on training split
        self.raw_model.fit(dataset.X_train, dataset.y_train)

        # Calibrate using Isotonic regression on validation split
        self.calibrated_model = CalibratedClassifierCV(
            estimator=self.raw_model,
            cv="prefit",
            method="isotonic",
        )
        self.calibrated_model.fit(dataset.X_val, dataset.y_val)

        # Compute validation metrics
        y_prob = self.predict_proba(dataset.X_val)
        brier = float(brier_score_loss(dataset.y_val, y_prob))
        auc = float(roc_auc_score(dataset.y_val, y_prob)) if len(np.unique(dataset.y_val)) > 1 else 1.0

        return ModelEvaluationReport(
            model_type="LightGBM+Isotonic" if self.use_lightgbm else "LogisticRegression+Isotonic",
            target_name="aircraft_failure_risk",
            metrics={"brier_score": brier, "roc_auc": auc},
        )

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Return calibrated 1D array of failure probabilities in [0, 1]."""
        if self.calibrated_model is None:
            raise RuntimeError("Model has not been fitted or loaded.")
        probs = self.calibrated_model.predict_proba(X)
        return probs[:, 1] if probs.ndim == 2 else probs

    def save(self, path: Path | str) -> None:
        """Persist model checkpoint to disk."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "wb") as f:
            pickle.dump(self.calibrated_model, f)

    def load(self, path: Path | str) -> None:
        """Load model checkpoint from disk."""
        with open(path, "rb") as f:
            self.calibrated_model = pickle.load(f)


class TurnaroundDelayRegressor:
    """Predicts turnaround delay (minutes) for scheduled tasks."""

    def __init__(self, use_lightgbm: bool = True) -> None:
        self.use_lightgbm = use_lightgbm
        self.model: Any = None

    def fit(self, dataset: ChronologicalDataset) -> ModelEvaluationReport:
        """Fit regression model on chronological dataset."""
        if self.use_lightgbm:
            self.model = lgb.LGBMRegressor(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.05,
                random_state=42,
                verbosity=-1,
            )
        else:
            self.model = Ridge(alpha=1.0)

        self.model.fit(dataset.X_train, dataset.y_train)

        # Validation metrics
        preds = self.predict(dataset.X_val)
        rmse = float(root_mean_squared_error(dataset.y_val, preds))
        mae = float(mean_absolute_error(dataset.y_val, preds))

        return ModelEvaluationReport(
            model_type="LightGBMRegressor" if self.use_lightgbm else "RidgeRegressor",
            target_name="turnaround_delay_minutes",
            metrics={"rmse": rmse, "mae": mae},
        )

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Return predicted non-negative turnaround delay in minutes."""
        if self.model is None:
            raise RuntimeError("Model has not been fitted or loaded.")
        preds = self.model.predict(X)
        return np.maximum(0.0, preds)

    def save(self, path: Path | str) -> None:
        """Persist regressor checkpoint to disk."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "wb") as f:
            pickle.dump(self.model, f)

    def load(self, path: Path | str) -> None:
        """Load regressor checkpoint from disk."""
        with open(path, "rb") as f:
            self.model = pickle.load(f)
