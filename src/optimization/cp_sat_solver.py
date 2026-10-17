"""Primary Google OR-Tools CP-SAT Optimization Solver Implementation.

This module provides the production CP-SAT constraint programming solver
implementing the SolverInterface. It handles model building, multi-threaded
search, primal solution extraction, timeout enforcement, and diagnostic telemetry.
"""

from __future__ import annotations

import time
from typing import Any

from ortools.sat.python import cp_model

from src.optimization.constraints import ConstraintBuilder
from src.optimization.objectives import ObjectiveBuilder
from src.optimization.solver_config import SolverConfig
from src.optimization.solver_interface import (
    OptimizationResult,
    SolverInterface,
    SolverStatus,
    TaskAssignment,
)


class CPSatOptimizationSolver(SolverInterface):
    """Google OR-Tools CP-SAT solver for multi-resource air operations scheduling."""

    def __init__(self, solver_name: str = "Google_OR_Tools_CP_SAT") -> None:
        self.solver_name = solver_name

    def solve(
        self,
        state: Any,
        config: SolverConfig | None = None,
        risk_profile: dict[str, float] | None = None,
        baseline_assignments: dict[str, str] | None = None,
    ) -> OptimizationResult:
        """Solve the resource allocation and scheduling problem using CP-SAT.

        Args:
            state: CanonicalOperationalState object or raw state dictionary.
            config: Solver runtime limits, weights, and parameters.
            risk_profile: Optional dictionary mapping aircraft_id to failure probability.
            baseline_assignments: Optional baseline mapping task_id to previous aircraft_id.

        Returns:
            OptimizationResult containing status, assignments, objective score, and metrics.
        """
        if config is None:
            config = SolverConfig()

        start_time = time.perf_counter()

        # Normalize state collections into lists of dictionaries
        tasks, aircraft, crew, airbases, maintenance_windows = self._extract_collections(state)

        if not tasks:
            return OptimizationResult(
                status=SolverStatus.OPTIMAL,
                objective_value=0.0,
                runtime_seconds=time.perf_counter() - start_time,
                solver_name=self.solver_name,
            )

        model = cp_model.CpModel()
        builder = ConstraintBuilder(model)

        # 1. Build Decision Variables
        builder.build_decision_variables(tasks, aircraft, crew)

        # 2. Add Hard Operational Constraints
        builder.add_assignment_uniqueness_constraints(tasks, aircraft, crew)
        builder.add_capability_and_qualification_constraints(tasks, aircraft, crew)
        builder.add_aircraft_no_overlap_constraints(tasks, aircraft)
        builder.add_crew_duty_and_rest_constraints(tasks, crew)

        if airbases:
            builder.add_runway_slot_capacity_constraints(tasks, airbases)
        if maintenance_windows:
            builder.add_maintenance_lockout_constraints(tasks, maintenance_windows)

        # 3. Add Scaled Objective Function
        obj_builder = ObjectiveBuilder(model, builder)
        obj_builder.build_composite_objective(
            tasks=tasks,
            aircraft=aircraft,
            config=config,
            risk_profile=risk_profile,
            baseline_assignments=baseline_assignments,
        )

        # 4. Configure CP-SAT Solver Parameters
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(config.time_limit_seconds)
        solver.parameters.num_search_workers = int(config.num_search_workers)
        solver.parameters.log_search_progress = bool(config.log_search_progress)
        solver.parameters.random_seed = int(config.random_seed)

        # 5. Execute Optimization Search
        raw_status = solver.Solve(model)
        elapsed_time = time.perf_counter() - start_time

        # 6. Map Terminal Status and Extract Primal Solution
        status = self._map_status(raw_status)
        assignments: list[TaskAssignment] = []
        unassigned: list[str] = []
        infeasibility_reasons: list[str] = []

        if status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
            for t in tasks:
                tid = t["task_id"]
                is_fulfilled = bool(solver.Value(builder.u[tid]))
                if is_fulfilled:
                    assigned_ac = None
                    for ac in aircraft:
                        aid = ac["aircraft_id"]
                        if solver.Value(builder.x[(tid, aid)]) == 1:
                            assigned_ac = aid
                            break

                    assigned_cr = None
                    for cr in crew:
                        cid = cr["crew_id"]
                        if solver.Value(builder.y[(tid, cid)]) == 1:
                            assigned_cr = cid
                            break

                    scheduled_start = int(solver.Value(builder.start_vars[tid]))
                    scheduled_end = int(solver.Value(builder.end_vars[tid]))
                    delay = int(solver.Value(builder.delay_vars[tid]))

                    assignments.append(
                        TaskAssignment(
                            task_id=tid,
                            aircraft_id=str(assigned_ac),
                            crew_id=str(assigned_cr),
                            scheduled_start_minute=scheduled_start,
                            scheduled_end_minute=scheduled_end,
                            delay_minutes=delay,
                        )
                    )
                else:
                    unassigned.append(tid)

            objective_val = float(solver.ObjectiveValue())
            best_bound = float(solver.BestObjectiveBound())
            gap = 0.0
            if status != SolverStatus.OPTIMAL and abs(objective_val) > 1e-6:
                gap = abs(objective_val - best_bound) / abs(objective_val)

        else:
            objective_val = 0.0
            best_bound = 0.0
            gap = 0.0
            unassigned = [t["task_id"] for t in tasks]
            if status == SolverStatus.INFEASIBLE:
                infeasibility_reasons.append(
                    "Mathematical infeasibility: Hard constraints cannot be satisfied with available resources."
                )

        # 7. Automated Infeasibility & Bottleneck Diagnosis
        diagnostic_report = None
        if unassigned or status == SolverStatus.INFEASIBLE:
            from src.optimization.diagnostics import InfeasibilityDiagnoser

            diagnostic_report = InfeasibilityDiagnoser.diagnose(
                tasks=tasks,
                aircraft=aircraft,
                crew=crew,
                airbases=airbases,
                maintenance_windows=maintenance_windows,
                unassigned_task_ids=unassigned,
            )
            infeasibility_reasons.extend(diagnostic_report.explanations)

        diag_metrics = {
            "wall_time": solver.WallTime(),
            "user_time": solver.UserTime(),
            "branches": solver.NumBranches(),
            "conflicts": solver.NumConflicts(),
        }
        if diagnostic_report:
            diag_metrics["diagnostic_report"] = diagnostic_report.to_dict()

        return OptimizationResult(
            status=status,
            objective_value=objective_val,
            best_bound=best_bound,
            optimality_gap=gap,
            runtime_seconds=elapsed_time,
            assignments=assignments,
            unassigned_task_ids=unassigned,
            infeasibility_reasons=infeasibility_reasons,
            solver_name=self.solver_name,
            diagnostic_metrics=diag_metrics,
        )

    def _map_status(self, raw_status: int) -> SolverStatus:
        if raw_status == cp_model.OPTIMAL:
            return SolverStatus.OPTIMAL
        if raw_status == cp_model.FEASIBLE:
            return SolverStatus.FEASIBLE
        if raw_status == cp_model.INFEASIBLE:
            return SolverStatus.INFEASIBLE
        if raw_status == cp_model.MODEL_INVALID:
            return SolverStatus.MODEL_INVALID
        return SolverStatus.UNKNOWN

    def _extract_collections(self, state: Any) -> tuple[list, list, list, list, list]:
        """Normalize state into tasks, aircraft, crew, airbases, maintenance_windows."""
        tasks, aircraft, crew, airbases, maintenance = [], [], [], [], []

        if hasattr(state, "tasks"):
            raw_tasks = state.tasks.values() if isinstance(state.tasks, dict) else state.tasks
            tasks = [t.model_dump() if hasattr(t, "model_dump") else (t if isinstance(t, dict) else t.__dict__) for t in raw_tasks]
        elif isinstance(state, dict) and "tasks" in state:
            tasks = state["tasks"]

        if hasattr(state, "aircraft"):
            raw_ac = state.aircraft.values() if isinstance(state.aircraft, dict) else state.aircraft
            aircraft = [a.model_dump() if hasattr(a, "model_dump") else (a if isinstance(a, dict) else a.__dict__) for a in raw_ac]
        elif isinstance(state, dict) and "aircraft" in state:
            aircraft = state["aircraft"]

        if hasattr(state, "crew"):
            raw_cr = state.crew.values() if isinstance(state.crew, dict) else state.crew
            crew = [c.model_dump() if hasattr(c, "model_dump") else (c if isinstance(c, dict) else c.__dict__) for c in raw_cr]
        elif isinstance(state, dict) and "crew" in state:
            crew = state["crew"]

        if hasattr(state, "airbases"):
            raw_ab = state.airbases.values() if isinstance(state.airbases, dict) else state.airbases
            airbases = [b.model_dump() if hasattr(b, "model_dump") else (b if isinstance(b, dict) else b.__dict__) for b in raw_ab]
        elif isinstance(state, dict) and "airbases" in state:
            airbases = state["airbases"]

        if hasattr(state, "maintenance_windows"):
            maintenance = state.maintenance_windows
        elif isinstance(state, dict) and "maintenance_windows" in state:
            maintenance = state["maintenance_windows"]

        return tasks, aircraft, crew, airbases, maintenance
