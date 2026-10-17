"""Unit Tests for Google OR-Tools CP-SAT Solver Implementation.

Verifies:
1. Nominal multi-task assignment feasibility and optimality.
2. Capability and qualification compatibility filtering.
3. Strict non-overlapping interval disjunction on aircraft.
4. Crew flight duty hour limits and mandatory rest windows.
5. Infeasible/over-constrained scenario handling without crashes.
6. Search timeout adherence.
"""

from typing import Any

import pytest

from src.optimization.cp_sat_solver import CPSatOptimizationSolver
from src.optimization.solver_config import SolverConfig
from src.optimization.solver_interface import SolverStatus


@pytest.fixture
def nominal_state() -> dict[str, Any]:
    """Provides a small, clean, feasible air operations scenario."""
    aircraft = [
        {
            "aircraft_id": "AC-101",
            "type_id": "TYPE-CARGO",
            "capability_class": "HEAVY_CARGO",
            "nominal_turnaround_minutes": 30,
        },
        {
            "aircraft_id": "AC-102",
            "type_id": "TYPE-INTERCEPT",
            "capability_class": "FAST_INTERCEPT",
            "nominal_turnaround_minutes": 45,
        },
    ]

    crew = [
        {
            "crew_id": "CREW-01",
            "certified_classes": ["HEAVY_CARGO"],
            "max_duty_minutes_24h": 480,
            "min_rest_minutes": 720,
        },
        {
            "crew_id": "CREW-02",
            "certified_classes": ["FAST_INTERCEPT"],
            "max_duty_minutes_24h": 480,
            "min_rest_minutes": 720,
        },
    ]

    tasks = [
        {
            "task_id": "TASK-01",
            "priority": 100,
            "required_capability": "HEAVY_CARGO",
            "earliest_start_minute": 0,
            "latest_start_minute": 120,
            "duration_minutes": 120,
            "origin_base_id": "BASE-ALPHA",
            "dest_base_id": "BASE-BETA",
        },
        {
            "task_id": "TASK-02",
            "priority": 80,
            "required_capability": "FAST_INTERCEPT",
            "earliest_start_minute": 60,
            "latest_start_minute": 180,
            "duration_minutes": 90,
            "origin_base_id": "BASE-ALPHA",
            "dest_base_id": "BASE-ALPHA",
        },
    ]

    airbases = [
        {"airbase_id": "BASE-ALPHA", "max_hourly_movements": 10},
        {"airbase_id": "BASE-BETA", "max_hourly_movements": 10},
    ]

    return {
        "aircraft": aircraft,
        "crew": crew,
        "tasks": tasks,
        "airbases": airbases,
    }


class TestCPSatSolver:
    """Test suite for CPSatOptimizationSolver."""

    def test_solve_nominal_scenario(self, nominal_state: dict[str, Any]) -> None:
        solver = CPSatOptimizationSolver()
        config = SolverConfig(time_limit_seconds=5.0, num_search_workers=2)

        result = solver.solve(state=nominal_state, config=config)

        assert result.is_successful is True
        assert result.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        assert result.total_scheduled_tasks == 2
        assert result.total_unassigned_tasks == 0

        # Verify correct assignments
        assign_t1 = result.get_assignment_for_task("TASK-01")
        assert assign_t1 is not None
        assert assign_t1.aircraft_id == "AC-101"
        assert assign_t1.crew_id == "CREW-01"

        assign_t2 = result.get_assignment_for_task("TASK-02")
        assert assign_t2 is not None
        assert assign_t2.aircraft_id == "AC-102"
        assert assign_t2.crew_id == "CREW-02"

    def test_capability_mismatch_prevents_unfit_assignment(self) -> None:
        """When an aircraft lacks capability, it cannot be assigned."""
        state = {
            "aircraft": [
                {"aircraft_id": "AC-201", "capability_class": "FAST_INTERCEPT", "nominal_turnaround_minutes": 30}
            ],
            "crew": [
                {"crew_id": "CR-01", "certified_classes": ["HEAVY_CARGO"]}
            ],
            "tasks": [
                {
                    "task_id": "TASK-HEAVY",
                    "priority": 100,
                    "required_capability": "HEAVY_CARGO",
                    "earliest_start_minute": 0,
                    "latest_start_minute": 60,
                    "duration_minutes": 60,
                }
            ],
        }

        solver = CPSatOptimizationSolver()
        result = solver.solve(state=state, config=SolverConfig(time_limit_seconds=2.0))

        # AC-201 cannot fly HEAVY_CARGO task
        assert result.total_scheduled_tasks == 0
        assert "TASK-HEAVY" in result.unassigned_task_ids

    def test_aircraft_no_overlap_with_turnaround(self) -> None:
        """An aircraft assigned two tasks must execute them non-overlapping with turnaround."""
        state = {
            "aircraft": [
                {
                    "aircraft_id": "AC-SOLO",
                    "capability_class": "TACTICAL",
                    "nominal_turnaround_minutes": 60,  # 1 hour turnaround
                }
            ],
            "crew": [
                {
                    "crew_id": "CR-01",
                    "certified_classes": ["TACTICAL"],
                    "max_duty_minutes_24h": 600,
                    "min_rest_minutes": 0,  # disable rest buffer to isolate aircraft turnaround
                }
            ],
            "tasks": [
                {
                    "task_id": "T-ALPHA",
                    "priority": 100,
                    "required_capability": "TACTICAL",
                    "earliest_start_minute": 0,
                    "latest_start_minute": 300,
                    "duration_minutes": 120,  # 2 hours
                },
                {
                    "task_id": "T-BRAVO",
                    "priority": 90,
                    "required_capability": "TACTICAL",
                    "earliest_start_minute": 0,
                    "latest_start_minute": 300,
                    "duration_minutes": 120,  # 2 hours
                },
            ],
        }

        solver = CPSatOptimizationSolver()
        result = solver.solve(state=state, config=SolverConfig(time_limit_seconds=5.0))

        assert result.total_scheduled_tasks == 2
        a1 = result.get_assignment_for_task("T-ALPHA")
        a2 = result.get_assignment_for_task("T-BRAVO")
        assert a1 is not None and a2 is not None

        # Either T-ALPHA finishes before T-BRAVO starts + 60min turnaround, or vice versa
        if a1.scheduled_start_minute < a2.scheduled_start_minute:
            assert a2.scheduled_start_minute >= a1.scheduled_end_minute + 60
        else:
            assert a1.scheduled_start_minute >= a2.scheduled_end_minute + 60

    def test_crew_max_duty_hours_respected(self) -> None:
        """Crew cannot exceed max_duty_minutes_24h."""
        state = {
            "aircraft": [
                {"aircraft_id": "AC-1", "capability_class": "RECON", "nominal_turnaround_minutes": 10},
                {"aircraft_id": "AC-2", "capability_class": "RECON", "nominal_turnaround_minutes": 10},
            ],
            "crew": [
                {
                    "crew_id": "CR-SOLO",
                    "certified_classes": ["RECON"],
                    "max_duty_minutes_24h": 120,  # Pilot can only fly 2 hours total
                    "min_rest_minutes": 0,
                }
            ],
            "tasks": [
                {
                    "task_id": "TASK-1",
                    "priority": 100,
                    "required_capability": "RECON",
                    "earliest_start_minute": 0,
                    "latest_start_minute": 60,
                    "duration_minutes": 90,  # 1.5h
                },
                {
                    "task_id": "TASK-2",
                    "priority": 50,
                    "required_capability": "RECON",
                    "earliest_start_minute": 0,
                    "latest_start_minute": 60,
                    "duration_minutes": 90,  # 1.5h (90 + 90 = 180 > 120 limit)
                },
            ],
        }

        solver = CPSatOptimizationSolver()
        result = solver.solve(state=state, config=SolverConfig(time_limit_seconds=3.0))

        # Only one task can be scheduled because 180 > 120 max duty
        assert result.total_scheduled_tasks == 1
        assert result.total_unassigned_tasks == 1
        # Highest priority task TASK-1 should be scheduled
        assert result.get_assignment_for_task("TASK-1") is not None

    def test_empty_tasks_returns_cleanly(self) -> None:
        solver = CPSatOptimizationSolver()
        result = solver.solve(state={"tasks": [], "aircraft": [], "crew": []})
        assert result.status == SolverStatus.OPTIMAL
        assert result.total_scheduled_tasks == 0
        assert result.objective_value == 0.0

    def test_timeout_enforcement(self) -> None:
        """Verify solver cleanly returns within configured search limit."""
        # Create a large task pool to force search
        tasks = [
            {
                "task_id": f"T-{i}",
                "priority": i * 10,
                "required_capability": "MULTI",
                "earliest_start_minute": 0,
                "latest_start_minute": 300,
                "duration_minutes": 60,
            }
            for i in range(25)
        ]
        aircraft = [
            {"aircraft_id": f"AC-{i}", "capability_class": "MULTI", "nominal_turnaround_minutes": 30}
            for i in range(5)
        ]
        crew = [
            {"crew_id": f"CR-{i}", "certified_classes": ["MULTI"], "max_duty_minutes_24h": 480, "min_rest_minutes": 60}
            for i in range(5)
        ]

        state = {"tasks": tasks, "aircraft": aircraft, "crew": crew}
        solver = CPSatOptimizationSolver()
        config = SolverConfig(time_limit_seconds=1.5, num_search_workers=2)

        result = solver.solve(state=state, config=config)

        # Must terminate within roughly 2.5s maximum
        assert result.runtime_seconds <= 3.0
        assert result.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE, SolverStatus.UNKNOWN)
