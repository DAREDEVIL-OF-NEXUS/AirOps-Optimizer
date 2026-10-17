"""Unit and Integration Tests for Risk-Aware Optimization Scheduling.

Verifies that the RiskAwareOptimizationSolver:
1. Penalizes and steers high-priority sorties away from high-risk airframes.
2. Injects dynamic delay buffers into task duration schedules.
3. Preserves schedule feasibility under varying risk profiles.
"""

from __future__ import annotations

from src.optimization.risk_aware_solver import RiskAwareOptimizationSolver
from src.optimization.solver_config import SolverConfig
from src.optimization.solver_interface import SolverStatus
from src.prediction.service import DisruptionRiskProfile


class TestRiskAwareSolver:
    """Tests the interaction between predictive models and mathematical optimization."""

    def test_risk_penalty_diverts_critical_mission_to_safer_airframe(self) -> None:
        """When two identical aircraft are available, the solver MUST choose the low-risk airframe."""
        solver = RiskAwareOptimizationSolver()

        tasks = [
            {
                "task_id": "CRITICAL_SORTIE",
                "earliest_start_minute": 100,
                "latest_start_minute": 100,
                "duration_minutes": 120,
                "priority": 5.0,  # High priority
                "required_capability": "FAST_JET",
            }
        ]

        # Two identical aircraft
        aircraft = [
            {"aircraft_id": "RISKY_AIRFRAME", "capability_class": "FAST_JET", "nominal_turnaround_minutes": 30},
            {"aircraft_id": "SAFE_AIRFRAME", "capability_class": "FAST_JET", "nominal_turnaround_minutes": 30},
        ]

        crew = [
            {"crew_id": "PILOT_TOP_GUN", "certified_classes": ["FAST_JET"], "max_duty_minutes_24h": 480}
        ]

        state = {"tasks": tasks, "aircraft": aircraft, "crew": crew}

        # Explicit risk profile: RISKY_AIRFRAME has 95% failure chance, SAFE_AIRFRAME has 2%
        risk_profile = DisruptionRiskProfile(
            aircraft_failure_probabilities={"RISKY_AIRFRAME": 0.95, "SAFE_AIRFRAME": 0.02},
            task_turnaround_delays={"CRITICAL_SORTIE": 0.0},
        )

        config = SolverConfig(
            weight_priority=1000,
            weight_risk=2000,  # High risk aversion
        )

        result = solver.solve(state, config=config, risk_profile=risk_profile)

        assert result.is_successful is True
        assert result.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        assert len(result.assignments) == 1
        # The solver MUST have selected SAFE_AIRFRAME due to the steep risk penalty
        assigned_ac = result.assignments[0].aircraft_id
        assert assigned_ac == "SAFE_AIRFRAME"

    def test_dynamic_delay_buffer_injection(self) -> None:
        """Verifies that predicted turnaround delays inflate the task's schedule buffer."""
        solver = RiskAwareOptimizationSolver()

        tasks = [
            {
                "task_id": "SORTIE_1",
                "earliest_start_minute": 0,
                "latest_start_minute": 60,
                "duration_minutes": 60,
                "priority": 2.0,
            }
        ]
        aircraft = [{"aircraft_id": "A1"}]
        crew = [{"crew_id": "C1"}]
        state = {"tasks": tasks, "aircraft": aircraft, "crew": crew}

        # Predict a 40 minute turnaround delay
        risk_profile = DisruptionRiskProfile(
            aircraft_failure_probabilities={"A1": 0.1},
            task_turnaround_delays={"SORTIE_1": 40.0},
        )

        result = solver.solve(state, risk_profile=risk_profile)
        assert result.is_successful is True
        assert len(result.assignments) == 1
        # Task duration was augmented with buffer (ceil(40 * 0.5) = 20) -> duration = 80
        assignment = result.assignments[0]
        assert assignment.duration_minutes == 80
