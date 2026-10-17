"""Unit Tests for Temporal Leakage Guards and Feature Pipeline.

Asserts that no future timestamps (t > t_cut) can bleed into the feature matrices,
and verifies chronological train/test split ordering.
"""

from __future__ import annotations

from src.prediction.features import PredictiveFeaturePipeline
from src.prediction.train import ChronologicalSplitGenerator


class TestLeakageGuards:
    """Verifies strict temporal cutoff boundaries."""

    def test_future_events_ignored_by_feature_pipeline(self) -> None:
        state = {
            "aircraft": [
                {"aircraft_id": "A1", "flight_hours": 100.0, "total_cycles": 50, "last_maintenance_minute": 0.0}
            ],
            "history": [
                # Event 1: Valid past event
                {"aircraft_id": "A1", "timestamp_minute": 100.0, "flight_duration_hours": 2.0, "cycles": 1, "event_type": "SORTIE_COMPLETED"},
                # Event 2: FUTURE event that occurred AFTER cutoff (t = 200 > t_cut = 150)
                {"aircraft_id": "A1", "timestamp_minute": 200.0, "flight_duration_hours": 10.0, "cycles": 5, "event_type": "SORTIE_COMPLETED"},
            ],
            "tasks": [],
        }

        # Cutoff set to minute 150
        feat_matrix = PredictiveFeaturePipeline.extract_aircraft_failure_features(
            state=state,
            cutoff_minute=150.0,
        )

        assert feat_matrix.X.shape[0] == 1
        hours_feature = feat_matrix.X[0, 0]
        cycles_feature = feat_matrix.X[0, 1]

        # Base hours (100) + Event 1 (2.0) = 102.0. Event 2 (10.0) MUST NOT be included.
        assert hours_feature == 102.0
        # Base cycles (50) + Event 1 (1) = 51. Event 2 (5) MUST NOT be included.
        assert cycles_feature == 51.0

    def test_future_maintenance_event_clamped_to_zero(self) -> None:
        state = {
            "aircraft": [
                {"aircraft_id": "A1", "flight_hours": 50.0, "last_maintenance_minute": 500.0}
            ],
            "history": [],
            "tasks": [],
        }

        # Cutoff is 300, but last_maintenance_minute is 500 (future anomaly)
        feat_matrix = PredictiveFeaturePipeline.extract_aircraft_failure_features(
            state=state,
            cutoff_minute=300.0,
        )

        # time_since_maint is feature index 2; should be max(0, 300 - 0) = 300.0
        assert feat_matrix.X[0, 2] == 300.0

    def test_chronological_split_generator_ordering(self) -> None:
        ds_fail, ds_delay = ChronologicalSplitGenerator.generate_synthetic_training_corpus(
            num_aircraft=20,
            num_days=10,
            split_ratio=0.75,
        )

        total_fail = ds_fail.X_train.shape[0] + ds_fail.X_val.shape[0]
        assert total_fail == 200
        assert ds_fail.X_train.shape[0] == 150
        assert ds_fail.X_val.shape[0] == 50
        assert len(ds_fail.feature_names) == 8

        total_delay = ds_delay.X_train.shape[0] + ds_delay.X_val.shape[0]
        assert total_delay == 400
        assert ds_delay.X_train.shape[0] == 300
        assert ds_delay.X_val.shape[0] == 100
        assert len(ds_delay.feature_names) == 8
