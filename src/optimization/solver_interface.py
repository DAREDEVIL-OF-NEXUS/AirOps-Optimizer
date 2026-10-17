"""Abstract Optimization Solver Interface and Core Data Transfer Contracts.

This module defines the public contracts, result envelopes, and status enumerations
for all resource allocation and scheduling solvers in AIRWISE. Solvers (CP-SAT,
Greedy baseline, MILP) implement the SolverInterface to ensure caller decoupling.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class SolverStatus(str, Enum):
    """Enumeration of terminal mathematical solver status states."""

    OPTIMAL = "OPTIMAL"
    """Proven global optimal solution found within search limits."""

    FEASIBLE = "FEASIBLE"
    """Valid feasible solution found; optimality gap unproven or non-zero."""

    INFEASIBLE = "INFEASIBLE"
    """Proven mathematical infeasibility; constraints cannot be satisfied."""

    MODEL_INVALID = "MODEL_INVALID"
    """Problem specification or parameter configuration is mathematically invalid."""

    UNKNOWN = "UNKNOWN"
    """Search completed or timed out without finding a feasible solution or proof of infeasibility."""


@dataclass(frozen=True)
class TaskAssignment:
    """Represents a discrete assignment of an aircraft and crew member to a task.

    Attributes:
        task_id: Unique identifier of the scheduled task.
        aircraft_id: Assigned aircraft airframe identifier.
        crew_id: Assigned crew member identifier.
        scheduled_start_minute: Scheduled departure minute from simulation epoch.
        scheduled_end_minute: Scheduled completion minute from simulation epoch.
        delay_minutes: Schedule delay beyond the earliest preferred start time.
        turnaround_buffer_minutes: Ground turnaround buffer applied after completion.
        metadata: Arbitrary operational annotations (e.g. priority, risk scores).
    """

    task_id: str
    aircraft_id: str
    crew_id: str
    scheduled_start_minute: int
    scheduled_end_minute: int
    delay_minutes: int = 0
    turnaround_buffer_minutes: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.scheduled_end_minute < self.scheduled_start_minute:
            raise ValueError(
                f"scheduled_end_minute ({self.scheduled_end_minute}) cannot be earlier "
                f"than scheduled_start_minute ({self.scheduled_start_minute}) for task '{self.task_id}'."
            )
        if self.delay_minutes < 0:
            raise ValueError(f"delay_minutes ({self.delay_minutes}) must be non-negative.")

    @property
    def duration_minutes(self) -> int:
        """Total scheduled duration of the flight leg in minutes."""
        return self.scheduled_end_minute - self.scheduled_start_minute

    def to_dict(self) -> dict[str, Any]:
        """Serialize assignment record to a standard dictionary."""
        data = asdict(self)
        data["duration_minutes"] = self.duration_minutes
        return data


@dataclass
class OptimizationResult:
    """Comprehensive terminal result envelope returned by all AIRWISE solvers.

    Attributes:
        status: Terminal solver status (OPTIMAL, FEASIBLE, INFEASIBLE, UNKNOWN).
        objective_value: Evaluated composite objective score of the plan.
        best_bound: Dual mathematical bound established by the solver.
        optimality_gap: Relative or absolute optimality gap (0.0 for proven optimum).
        runtime_seconds: Elapsed wall-clock solver search time.
        assignments: List of fulfilled task assignments.
        unassigned_task_ids: List of tasks that could not be feasibly scheduled.
        infeasibility_reasons: Diagnostic explanations if infeasible or tasks unassigned.
        solver_name: Identifier of the solver that generated the result.
        diagnostic_metrics: Arbitrary solver telemetry (branch count, memory, cuts).
    """

    status: SolverStatus
    objective_value: float = 0.0
    best_bound: float = 0.0
    optimality_gap: float = 0.0
    runtime_seconds: float = 0.0
    assignments: list[TaskAssignment] = field(default_factory=list)
    unassigned_task_ids: list[str] = field(default_factory=list)
    infeasibility_reasons: list[str] = field(default_factory=list)
    solver_name: str = "AbstractSolver"
    diagnostic_metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def is_successful(self) -> bool:
        """True if a valid feasible or optimal plan was produced."""
        return self.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)

    @property
    def total_scheduled_tasks(self) -> int:
        """Count of successfully scheduled tasks."""
        return len(self.assignments)

    @property
    def total_unassigned_tasks(self) -> int:
        """Count of unassigned or rejected tasks."""
        return len(self.unassigned_task_ids)

    def get_assignment_for_task(self, task_id: str) -> TaskAssignment | None:
        """Retrieve assignment record for a specific task ID, if present."""
        for assignment in self.assignments:
            if assignment.task_id == task_id:
                return assignment
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize complete optimization result to dictionary."""
        return {
            "status": self.status.value,
            "objective_value": self.objective_value,
            "best_bound": self.best_bound,
            "optimality_gap": self.optimality_gap,
            "runtime_seconds": self.runtime_seconds,
            "assignments": [a.to_dict() for a in self.assignments],
            "unassigned_task_ids": list(self.unassigned_task_ids),
            "infeasibility_reasons": list(self.infeasibility_reasons),
            "solver_name": self.solver_name,
            "diagnostic_metrics": dict(self.diagnostic_metrics),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OptimizationResult:
        """Deserialize dictionary into an OptimizationResult instance."""
        raw_assignments = data.get("assignments", [])
        valid_fields = TaskAssignment.__dataclass_fields__.keys()
        assignments = [
            TaskAssignment(**{k: v for k, v in a.items() if k in valid_fields})
            if isinstance(a, dict)
            else a
            for a in raw_assignments
        ]
        status = SolverStatus(data.get("status", "UNKNOWN"))
        return cls(
            status=status,
            objective_value=float(data.get("objective_value", 0.0)),
            best_bound=float(data.get("best_bound", 0.0)),
            optimality_gap=float(data.get("optimality_gap", 0.0)),
            runtime_seconds=float(data.get("runtime_seconds", 0.0)),
            assignments=assignments,
            unassigned_task_ids=list(data.get("unassigned_task_ids", [])),
            infeasibility_reasons=list(data.get("infeasibility_reasons", [])),
            solver_name=str(data.get("solver_name", "AbstractSolver")),
            diagnostic_metrics=dict(data.get("diagnostic_metrics", {})),
        )


class SolverInterface(ABC):
    """Abstract Base Class defining the contract for all optimization solvers."""

    @abstractmethod
    def solve(self, state: Any, config: Any) -> OptimizationResult:
        """Solve the resource allocation and scheduling problem.

        Args:
            state: Canonical operational state containing assets, crews, and tasks.
            config: Solver runtime limits, objective weights, and seed parameters.

        Returns:
            OptimizationResult containing schedule assignments, metrics, status,
            and diagnostics.
        """
        raise NotImplementedError("Solvers must implement the solve method.")
