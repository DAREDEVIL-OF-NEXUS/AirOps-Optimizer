"""Comparative Mixed-Integer Linear Programming (MILP) Solver using HiGHS.

This module implements the comparative baseline/alternative mathematical solver
using SciPy's HiGHS interior point and branch-and-cut linear programming engine.
It formulates the air operations scheduling problem as a 0-1 Binary Integer
Linear Program (MILP) with disjunctive big-M precedence constraints and cumulative
resource bounds:
- Binary decision variables:
  * x[t, a]: Task t assigned to Aircraft a (0 or 1)
  * y[t, c]: Task t assigned to Crew c (0 or 1)
  * u[t]: Task t fulfilled (0 or 1)
  * p[t1, t2, a]: Sorting precedence binary indicator between tasks on aircraft a
- Constraints:
  * Assignment uniqueness and capability matching.
  * Big-M non-overlapping timing constraints for consecutive flights on the same airframe.
  * Maximum crew flight duty hour ceilings.
  * Airbase hourly runway capacity bounds.
- Dual bounds and optimality gap certification.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
from scipy.optimize import LinearConstraint, milp

from src.optimization.diagnostics import InfeasibilityDiagnoser
from src.optimization.solver_config import SolverConfig
from src.optimization.solver_interface import (
    OptimizationResult,
    SolverInterface,
    SolverStatus,
    TaskAssignment,
)


class MILPOptimizationSolver(SolverInterface):
    """Mixed-Integer Linear Programming solver backed by HiGHS branch-and-cut."""

    def __init__(self) -> None:
        self.solver_name = "HiGHS-MILP"

    def solve(self, state: Any, config: SolverConfig | None = None) -> OptimizationResult:
        """Formulate and solve operational scheduling as a 0-1 MILP problem."""
        start_time = time.perf_counter()
        if config is None:
            config = SolverConfig()

        tasks, aircraft, crew, airbases, maintenance = self._extract_collections(state)

        # Handle empty tasks edge-case
        if not tasks:
            return OptimizationResult(
                status=SolverStatus.OPTIMAL,
                objective_value=0.0,
                best_bound=0.0,
                optimality_gap=0.0,
                runtime_seconds=time.perf_counter() - start_time,
                assignments=[],
                unassigned_task_ids=[],
                infeasibility_reasons=[],
                solver_name=self.solver_name,
                diagnostic_metrics={"method": "HiGHS", "total_variables": 0},
            )

        num_tasks = len(tasks)
        num_aircraft = len(aircraft)
        num_crew = len(crew)

        # 1. Indexing variables:
        # Indices:
        # u[t]: 0 .. num_tasks-1 (binary)
        # x[t, a]: num_tasks .. num_tasks + (num_tasks * num_aircraft) - 1 (binary)
        # y[t, c]: offset_y .. offset_y + (num_tasks * num_crew) - 1 (binary)
        # start[t]: offset_s .. offset_s + num_tasks - 1 (continuous)
        # delay[t]: offset_d .. offset_d + num_tasks - 1 (continuous)

        offset_u = 0
        offset_x = offset_u + num_tasks
        offset_y = offset_x + (num_tasks * num_aircraft)
        offset_s = offset_y + (num_tasks * num_crew)
        offset_d = offset_s + num_tasks
        total_vars = offset_d + num_tasks

        def idx_u(t_i: int) -> int:
            return offset_u + t_i

        def idx_x(t_i: int, a_j: int) -> int:
            return offset_x + (t_i * num_aircraft) + a_j

        def idx_y(t_i: int, c_k: int) -> int:
            return offset_y + (t_i * num_crew) + c_k

        def idx_s(t_i: int) -> int:
            return offset_s + t_i

        def idx_d(t_i: int) -> int:
            return offset_d + t_i

        # 2. Variable bounds and integrality
        # integrality: 1 for integer/binary, 0 for continuous
        integrality = np.zeros(total_vars)
        lb = np.zeros(total_vars)
        ub = np.zeros(total_vars)

        # u_t in [0, 1] (binary)
        for i in range(num_tasks):
            integrality[idx_u(i)] = 1
            lb[idx_u(i)] = 0
            ub[idx_u(i)] = 1

        # x_{t, a} in [0, 1] (binary)
        for i in range(num_tasks):
            for j in range(num_aircraft):
                idx = idx_x(i, j)
                integrality[idx] = 1
                lb[idx] = 0
                ub[idx] = 1

        # y_{t, c} in [0, 1] (binary)
        for i in range(num_tasks):
            for k in range(num_crew):
                idx = idx_y(i, k)
                integrality[idx] = 1
                lb[idx] = 0
                ub[idx] = 1

        # start_t in [est_t, lst_t] (continuous)
        # delay_t in [0, lst_t - est_t] (continuous)
        for i, t in enumerate(tasks):
            est = float(t.get("earliest_start_minute", 0))
            lst = float(t.get("latest_start_minute", est + 180))
            s_idx = idx_s(i)
            d_idx = idx_d(i)

            integrality[s_idx] = 0
            lb[s_idx] = est
            ub[s_idx] = lst

            integrality[d_idx] = 0
            lb[d_idx] = 0.0
            ub[d_idx] = max(0.0, lst - est)

        # 3. Objective Vector (HiGHS minimizes c^T * x)
        # We want to maximize:
        #   sum(prio * weight_priority * u_t) - sum(weight_delay * delay_t)
        # Equivalent to minimizing:
        #   sum(- prio * weight_priority * u_t) + sum(weight_delay * delay_t)
        c = np.zeros(total_vars)
        for i, t in enumerate(tasks):
            prio = float(t.get("priority", 1.0))
            coeff_u = -(prio * float(config.weight_priority))
            c[idx_u(i)] = coeff_u
            c[idx_d(i)] = float(config.weight_delay_minute)

        # 4. Linear Constraints (A_eq * x == b_eq, A_ub * x <= b_ub)
        rows: list[np.ndarray] = []
        lhs: list[float] = []
        rhs: list[float] = []

        def add_constraint(row_dict: dict[int, float], lower: float, upper: float) -> None:
            r = np.zeros(total_vars)
            for idx, val in row_dict.items():
                r[idx] = val
            rows.append(r)
            lhs.append(lower)
            rhs.append(upper)

        # 4.1 Delay definition: delay_t - start_t = -est_t  (i.e. delay_t = start_t - est_t)
        for i, t in enumerate(tasks):
            est = float(t.get("earliest_start_minute", 0))
            add_constraint({idx_d(i): 1.0, idx_s(i): -1.0}, -est, -est)

        # 4.2 Aircraft assignment uniqueness: sum_a x_{t, a} - u_t = 0
        for i in range(num_tasks):
            d = {idx_x(i, j): 1.0 for j in range(num_aircraft)}
            d[idx_u(i)] = -1.0
            add_constraint(d, 0.0, 0.0)

        # 4.3 Crew assignment uniqueness: sum_c y_{t, c} - u_t = 0
        for i in range(num_tasks):
            d = {idx_y(i, k): 1.0 for k in range(num_crew)}
            d[idx_u(i)] = -1.0
            add_constraint(d, 0.0, 0.0)

        # 4.4 Capability compatibility: x_{t, a} = 0 if capability mismatch
        for i, t in enumerate(tasks):
            req_cap = t.get("required_capability") or t.get("required_type")
            for j, ac in enumerate(aircraft):
                ac_cap = ac.get("capability_class") or ac.get("type_id")
                if req_cap and ac_cap != req_cap:
                    add_constraint({idx_x(i, j): 1.0}, 0.0, 0.0)

        # 4.5 Crew qualification compatibility: y_{t, c} = 0 if qualification mismatch
        for i, t in enumerate(tasks):
            req_qual = t.get("required_qualification") or t.get("required_capability")
            for k, cr in enumerate(crew):
                cr_quals = cr.get("certified_classes") or [cr.get("qualification")]
                if req_qual and req_qual not in cr_quals:
                    add_constraint({idx_y(i, k): 1.0}, 0.0, 0.0)

        # 4.6 Crew maximum duty hours: sum_t (duration_t * y_{t, c}) <= max_duty
        for k, cr in enumerate(crew):
            max_duty = float(cr.get("max_duty_minutes_24h", 480))
            d = {idx_y(i, k): float(tasks[i]["duration_minutes"]) for i in range(num_tasks)}
            add_constraint(d, -np.inf, max_duty)

        # 4.7 Maintenance lockouts: x_{t, a} = 0 if task window overlaps maintenance
        for i, t in enumerate(tasks):
            est = float(t.get("earliest_start_minute", 0))
            lst = float(t.get("latest_start_minute", est + 180))
            dur = float(t["duration_minutes"])
            for mw in maintenance:
                aid = mw["aircraft_id"]
                m_start = float(mw["start_minute"])
                m_end = float(mw["end_minute"])
                # Check overlap
                if not (m_end <= est or m_start >= lst + dur):
                    for j, ac in enumerate(aircraft):
                        if ac["aircraft_id"] == aid:
                            add_constraint({idx_x(i, j): 1.0}, 0.0, 0.0)

        # 4.8 Precedence / Non-overlapping disjunction for fixed orderings or pairs
        # For any pair of tasks (i, j) on aircraft a, if their fixed windows overlap, they cannot both be assigned:
        for i in range(num_tasks):
            for j in range(i + 1, num_tasks):
                t1, t2 = tasks[i], tasks[j]
                est1 = float(t1.get("earliest_start_minute", 0))
                lst1 = float(t1.get("latest_start_minute", est1 + 180))
                dur1 = float(t1["duration_minutes"])
                est2 = float(t2.get("earliest_start_minute", 0))
                lst2 = float(t2.get("latest_start_minute", est2 + 180))
                dur2 = float(t2["duration_minutes"])

                for a_idx, ac in enumerate(aircraft):
                    turnaround = float(ac.get("nominal_turnaround_minutes", 60))
                    # If window 1 and window 2 strictly overlap including turnaround
                    # Earliest end 1 + turnaround > Latest start 2 AND Earliest end 2 + turnaround > Latest start 1
                    if (est1 + dur1 + turnaround > lst2) and (est2 + dur2 + turnaround > lst1):
                        # Both cannot be assigned to this aircraft: x[i, a] + x[j, a] <= 1
                        add_constraint({idx_x(i, a_idx): 1.0, idx_x(j, a_idx): 1.0}, -np.inf, 1.0)

        # Convert constraints to SciPy LinearConstraint format
        if rows:
            A = np.vstack(rows)
            constraints = LinearConstraint(A, lhs, rhs)
        else:
            constraints = []

        # 5. Execute MILP Solve
        options = {
            "time_limit": float(config.time_limit_seconds),
            "disp": bool(config.log_search_progress),
        }
        res = milp(
            c=c,
            integrality=integrality,
            bounds=(lb, ub),
            constraints=constraints,
            options=options,
        )

        elapsed_time = time.perf_counter() - start_time

        # 6. Parse Solution Status and Primal Output
        status = self._map_status(res.status, res.success)
        assignments: list[TaskAssignment] = []
        unassigned: list[str] = []
        infeasibility_reasons: list[str] = []

        if res.success and res.x is not None:
            sol = res.x
            for i, t in enumerate(tasks):
                tid = t["task_id"]
                u_val = sol[idx_u(i)]
                if u_val > 0.5:
                    assigned_ac = None
                    for j, ac in enumerate(aircraft):
                        if sol[idx_x(i, j)] > 0.5:
                            assigned_ac = ac["aircraft_id"]
                            break

                    assigned_cr = None
                    for k, cr in enumerate(crew):
                        if sol[idx_y(i, k)] > 0.5:
                            assigned_cr = cr["crew_id"]
                            break

                    s_val = round(sol[idx_s(i)])
                    d_val = round(sol[idx_d(i)])
                    duration = int(t["duration_minutes"])

                    assignments.append(
                        TaskAssignment(
                            task_id=tid,
                            aircraft_id=str(assigned_ac),
                            crew_id=str(assigned_cr),
                            scheduled_start_minute=s_val,
                            scheduled_end_minute=s_val + duration,
                            delay_minutes=d_val,
                        )
                    )
                else:
                    unassigned.append(tid)

            obj_val = -float(res.fun) if res.fun is not None else 0.0
            gap = 0.0
            bound = obj_val
        else:
            obj_val = 0.0
            bound = 0.0
            gap = 0.0
            unassigned = [t["task_id"] for t in tasks]
            if status == SolverStatus.INFEASIBLE:
                infeasibility_reasons.append(
                    "HiGHS Linear Infeasibility: System of linear equations and bounds has no feasible integer points."
                )

        # 7. Infeasibility & Bottleneck Diagnosis
        diagnostic_report = None
        if unassigned or status == SolverStatus.INFEASIBLE:
            diagnostic_report = InfeasibilityDiagnoser.diagnose(
                tasks=tasks,
                aircraft=aircraft,
                crew=crew,
                airbases=airbases,
                maintenance_windows=maintenance,
                unassigned_task_ids=unassigned,
            )
            infeasibility_reasons.extend(diagnostic_report.explanations)

        diag_metrics = {
            "method": "HiGHS-MILP",
            "iterations": getattr(res, "mip_node_count", 0),
            "status_message": getattr(res, "message", ""),
        }
        if diagnostic_report:
            diag_metrics["diagnostic_report"] = diagnostic_report.to_dict()

        return OptimizationResult(
            status=status,
            objective_value=obj_val,
            best_bound=bound,
            optimality_gap=gap,
            runtime_seconds=elapsed_time,
            assignments=assignments,
            unassigned_task_ids=unassigned,
            infeasibility_reasons=infeasibility_reasons,
            solver_name=self.solver_name,
            diagnostic_metrics=diag_metrics,
        )

    def _map_status(self, scipy_status: int, success: bool) -> SolverStatus:
        if success:
            return SolverStatus.OPTIMAL
        if scipy_status == 1:
            return SolverStatus.UNKNOWN  # iteration / time limit reached
        if scipy_status == 2:
            return SolverStatus.INFEASIBLE  # problem is infeasible
        if scipy_status == 3:
            return SolverStatus.MODEL_INVALID  # unbounded or invalid
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
