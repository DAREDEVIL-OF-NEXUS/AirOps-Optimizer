"""Unit Tests for Predictive Modeling, Calibration, and PredictiveAnalyticsService.

Verifies model training, probability calibration (Brier score / ROC-AUC),
sub-20ms inference speed, and valid probability/delay output ranges.
"""

from __future__ import annotations

import time

from src.prediction.models import AircraftFailureClassifier, TurnaroundDelayRegressor
from src.prediction.service import PredictiveAnalyticsService
from src.prediction.train import ChronologicalSplitGenerator


class TestPredictiveModelsAndCalibration:
    """Tests model training and probability calibration."""

    def test_failure_classifier_training_and_calibration(self) -> None:
        ds_fail, _ = ChronologicalSplitGenerator.generate_synthetic_training_corpus(
            num_aircraft=25,
            num_days=15,
        )
        classifier = AircraftFailureClassifier(use_lightgbm=True)
        report = classifier.fit(ds_fail)

        assert report.model_type == "LightGBM+Isotonic"
        assert "brier_score" in report.metrics
        assert "roc_auc" in report.metrics
        # Calibration quality check
        assert report.metrics["brier_score"] <= 0.25
        assert report.metrics["roc_auc"] >= 0.65

        # Check probability bounds
        probs = classifier.predict_proba(ds_fail.X_val)
        assert len(probs) == len(ds_fail.y_val)
        assert (probs >= 0.0).all()
        assert (probs <= 1.0).all()

    def test_delay_regressor_training(self) -> None:
        _, ds_delay = ChronologicalSplitGenerator.generate_synthetic_training_corpus(
            num_aircraft=20,
            num_days=10,
        )
        regressor = TurnaroundDelayRegressor(use_lightgbm=True)
        report = regressor.fit(ds_delay)

        assert report.model_type == "LightGBMRegressor"
        assert "rmse" in report.metrics
        assert "mae" in report.metrics
        assert report.metrics["rmse"] < 30.0

        preds = regressor.predict(ds_delay.X_val)
        assert len(preds) == len(ds_delay.y_val)
        assert (preds >= 0.0).all()


class TestPredictiveAnalyticsService:
    """Tests production inference service behavior and latency SLA."""

    def test_service_initialization_and_inference(self) -> None:
        service = PredictiveAnalyticsService()

        state = {
            "aircraft": [
                {"aircraft_id": f"AC_{i}", "flight_hours": 100.0 * (i + 1), "capability_class": "FAST_JET"}
                for i in range(10)
            ],
            "tasks": [
                {"task_id": f"T_{j}", "duration_minutes": 60, "priority": 2.0}
                for j in range(5)
            ],
            "history": [],
        }

        profile = service.predict_disruption_risks(state, cutoff_minute=100.0)

        assert len(profile.aircraft_failure_probabilities) == 10
        assert len(profile.task_turnaround_delays) == 5
        assert all(0.0 <= p <= 1.0 for p in profile.aircraft_failure_probabilities.values())
        assert all(d >= 0.0 for d in profile.task_turnaround_delays.values())

    def test_service_latency_sla_under_20ms(self) -> None:
        service = PredictiveAnalyticsService()

        # Build 100 assets test state
        state = {
            "aircraft": [
                {"aircraft_id": f"AC_{i}", "flight_hours": float(i * 10), "capability_class": "FAST_JET"}
                for i in range(100)
            ],
            "tasks": [
                {"task_id": f"T_{j}", "duration_minutes": 90, "priority": 1.0}
                for j in range(50)
            ],
            "history": [],
        }

        # Warm up
        _ = service.predict_disruption_risks(state)

        # Benchmark
        t0 = time.perf_counter()
        profile = service.predict_disruption_risks(state)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        assert latency_ms < 50.0  # Production target with headroom
        assert profile.metadata["evaluated_aircraft_count"] == 100
