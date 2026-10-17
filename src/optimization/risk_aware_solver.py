"""Prediction-Aware Optimization Solver.

This module implements the RiskAwareOptimizationSolver, which connects the
calibrated machine-learning disruption predictions directly into the mathematical
scheduling engine:
1. Translates component failure probabilities P(fail) into dynamic risk penalties:
   penalty = weight_risk * sum_t (P(fail_a) * x[t, a]).
2. Dynamically inflates turnaround buffers based on expected delay predictions:
   Turnaround_effective = Turnaround_nominal + ceil(hat{Delta}_delay_t).
3. Intelligently steers critical high-priority sorties away from degrading airframes
   while maintaining strict mathematical feasibility of the overall schedule.
"""

from __future__ import annotations

import math
from typing import Any

from src.optimization.cp_sat_solver import CPSatOptimizationSolver
from src.optimization.solver_config import SolverConfig
from src.optimization.solver_interface import OptimizationResult, SolverInterface
from src.prediction.service import DisruptionRiskProfile, PredictiveAnalyticsService


class RiskAwareOptimizationSolver(SolverInterface):
    """High-level solver that couples ML predictive risk intelligence into CP-SAT."""

    def __init__(
        self,
        base_solver: CPSatOptimizationSolver | None = None,
        prediction_service: PredictiveAnalyticsService | None = None,
    ) -> None:
        self.solver_name = "RiskAware-CPSAT"
        self.base_solver = base_solver or CPSatOptimizationSolver()
        self.prediction_service = prediction_service or PredictiveAnalyticsService()

    def solve(
        self,
        state: Any,
        config: SolverConfig | None = None,
        risk_profile: DisruptionRiskProfile | None = None,
        baseline_assignments: dict[str, str] | None = None,
        cutoff_minute: float = 0.0,
    ) -> OptimizationResult:
        """Formulate and solve risk-penalized, delay-buffered flight schedule."""
        if config is None:
            config = SolverConfig()

        # 1. Obtain Disruption Risk Profile if not explicitly provided
        if risk_profile is None:
            risk_profile = self.prediction_service.predict_disruption_risks(
                state=state,
                cutoff_minute=cutoff_minute,
            )

        # 2. Inject dynamic turnaround buffers into state copy
        modified_state = self._inject_dynamic_buffers(state, risk_profile)

        # 3. Solve using CP-SAT with risk penalties
        result = self.base_solver.solve(
            state=modified_state,
            config=config,
            risk_profile=risk_profile.aircraft_failure_probabilities,
            baseline_assignments=baseline_assignments,
        )

        # 4. Enrich result metadata with predictive telemetries
        result.solver_name = self.solver_name
        result.diagnostic_metrics["predictive_intelligence"] = {
            "evaluated_risk_assets": len(risk_profile.aircraft_failure_probabilities),
            "dynamic_delays_applied": len(risk_profile.task_turnaround_delays),
            "inference_latency_ms": risk_profile.inference_latency_ms,
        }

        return result

    def _inject_dynamic_buffers(
        self,
        state: Any,
        risk_profile: DisruptionRiskProfile,
    ) -> dict[str, Any]:
        """Clone state and expand aircraft turnaround or task durations with buffer."""
        # Deep extract collections
        tasks, aircraft, crew, airbases, maintenance = self.base_solver._extract_collections(state)

        # Clone aircraft and inject task-specific turnaround adjustments if needed
        # Or inject predicted delays into tasks duration buffer
        modified_tasks = []
        for t in tasks:
            t_copy = dict(t)
            tid = t_copy["task_id"]
            if tid in risk_profile.task_turnaround_delays:
                extra_delay = risk_profile.task_turnaround_delays[tid]
                # Apply conservative safety padding to task duration
                buffer_mins = math.ceil(extra_delay * 0.5)
                t_copy["duration_minutes"] = int(t_copy["duration_minutes"]) + buffer_mins
                t_copy["turnaround_buffer_injected"] = buffer_mins
            modified_tasks.append(t_copy)

        return {
            "tasks": modified_tasks,
            "aircraft": aircraft,
            "crew": crew,
            "airbases": airbases,
            "maintenance_windows": maintenance,
        }
