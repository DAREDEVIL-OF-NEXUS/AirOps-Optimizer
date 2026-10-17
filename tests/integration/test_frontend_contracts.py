"""Integration Tests Validating Frontend Serialization Contracts.

Verifies that the data structures emitted by the optimization and prediction
subsystems strictly adhere to the schemas declared in docs/FRONTEND_HANDOFF.md.
"""

from __future__ import annotations

from src.optimization.diagnostics import InfeasibilityDiagnoser
from src.optimization.risk_aware_solver import RiskAwareOptimizationSolver
from src.prediction.service import PredictiveAnalyticsService


class TestFrontendContractsIntegration:
    """Verifies JSON schema shape compliance for frontend consumption."""

    def test_optimization_result_contract_shape(self) -> None:
        solver = RiskAwareOptimizationSolver()

        state = {
            "tasks": [
                {
                    "task_id": "T_TEST",
                    "earliest_start_minute": 60,
                    "latest_start_minute": 120,
                    "duration_minutes": 60,
                    "priority": 1.0,
                }
            ],
            "aircraft": [{"aircraft_id": "AC_01"}],
            "crew": [{"crew_id": "CR_01"}],
        }

        result = solver.solve(state)
        data = result.to_dict()

        # Assert top-level contract keys
        required_keys = {
            "status",
            "objective_value",
            "best_bound",
            "optimality_gap",
            "runtime_seconds",
            "assignments",
            "unassigned_task_ids",
            "infeasibility_reasons",
            "solver_name",
            "diagnostic_metrics",
        }
        assert required_keys.issubset(data.keys())

        # Assert assignment contract keys
        assert len(data["assignments"]) == 1
        assignment_keys = {
            "task_id",
            "aircraft_id",
            "crew_id",
            "scheduled_start_minute",
            "scheduled_end_minute",
            "delay_minutes",
            "turnaround_buffer_minutes",
            "duration_minutes",
            "metadata",
        }
        assert assignment_keys.issubset(data["assignments"][0].keys())

    def test_predictive_risk_profile_contract_shape(self) -> None:
        service = PredictiveAnalyticsService()

        state = {
            "aircraft": [{"aircraft_id": "AC_01"}],
            "tasks": [{"task_id": "T_01"}],
        }

        profile = service.predict_disruption_risks(state)
        data = profile.to_dict()

        required_profile_keys = {
            "aircraft_failure_probabilities",
            "task_turnaround_delays",
            "inference_latency_ms",
            "metadata",
        }
        assert required_profile_keys.issubset(data.keys())
        assert isinstance(data["aircraft_failure_probabilities"], dict)
        assert isinstance(data["task_turnaround_delays"], dict)
        assert isinstance(data["inference_latency_ms"], float)

    def test_infeasibility_report_contract_shape(self) -> None:
        report = InfeasibilityDiagnoser.diagnose(
            tasks=[{"task_id": "UNSAT_T", "duration_minutes": 9999}],
            aircraft=[{"aircraft_id": "AC_01"}],
            crew=[{"crew_id": "CR_01", "max_duty_minutes_24h": 480}],
            airbases=[],
            maintenance_windows=[],
            unassigned_task_ids=["UNSAT_T"],
        )
        data = report.to_dict()

        required_report_keys = {
            "is_feasible",
            "unassigned_task_count",
            "unassigned_task_ids",
            "bottlenecks",
            "explanations",
            "recommended_actions",
        }
        assert required_report_keys.issubset(data.keys())
        assert len(data["bottlenecks"]) > 0

        bottleneck_keys = {
            "category",
            "resource_id",
            "affected_task_ids",
            "description",
            "recommended_relaxation",
            "severity",
        }
        assert bottleneck_keys.issubset(data["bottlenecks"][0].keys())
