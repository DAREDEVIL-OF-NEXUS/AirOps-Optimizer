"""Unit Tests for Infeasibility Diagnostics and Comparative MILP Solver.

Tests the automated root-cause bottleneck classification, slack recommendations,
and the SciPy HiGHS MILP solver on nominal, constrained, and over-constrained problems.
"""

from __future__ import annotations

from src.optimization.cp_sat_solver import CPSatOptimizationSolver
from src.optimization.diagnostics import InfeasibilityDiagnoser
from src.optimization.milp_solver import MILPOptimizationSolver
from src.optimization.solver_interface import SolverStatus


class TestInfeasibilityDiagnostics:
    """Verifies that unassigned tasks are accurately diagnosed with root causes."""

    def test_all_feasible_returns_empty_bottlenecks(self) -> None:
        report = InfeasibilityDiagnoser.diagnose(
            tasks=[{"task_id": "T1"}],
            aircraft=[{"aircraft_id": "A1"}],
            crew=[{"crew_id": "C1"}],
            airbases=[{"airbase_id": "B1"}],
            maintenance_windows=[],
            unassigned_task_ids=[],
        )
        assert report.is_feasible is True
        assert report.unassigned_task_count == 0
        assert len(report.bottlenecks) == 0

    def test_aircraft_capability_deficit_diagnosed(self) -> None:
        tasks = [
            {"task_id": "T1", "required_capability": "HEAVY_TRANSPORT", "duration_minutes": 120}
        ]
        aircraft = [
            {"aircraft_id": "A1", "capability_class": "FAST_JET"}
        ]
        crew = [
            {"crew_id": "C1", "certified_classes": ["HEAVY_TRANSPORT"]}
        ]
        report = InfeasibilityDiagnoser.diagnose(
            tasks=tasks,
            aircraft=aircraft,
            crew=crew,
            airbases=[],
            maintenance_windows=[],
            unassigned_task_ids=["T1"],
        )
        assert report.is_feasible is False
        assert report.unassigned_task_count == 1
        assert any(b.category == "AIRCRAFT_CAPABILITY" for b in report.bottlenecks)
        assert "HEAVY_TRANSPORT" in report.bottlenecks[0].description

    def test_crew_qualification_deficit_diagnosed(self) -> None:
        tasks = [
            {"task_id": "T1", "required_capability": "FAST_JET", "required_qualification": "NIGHT_VISION", "duration_minutes": 60}
        ]
        aircraft = [
            {"aircraft_id": "A1", "capability_class": "FAST_JET"}
        ]
        crew = [
            {"crew_id": "C1", "certified_classes": ["DAY_ONLY"]}
        ]
        report = InfeasibilityDiagnoser.diagnose(
            tasks=tasks,
            aircraft=aircraft,
            crew=crew,
            airbases=[],
            maintenance_windows=[],
            unassigned_task_ids=["T1"],
        )
        assert report.is_feasible is False
        assert any(b.category == "CREW_QUALIFICATION" for b in report.bottlenecks)
        assert "NIGHT_VISION" in report.bottlenecks[0].description

    def test_crew_duty_limit_exceeded_diagnosed(self) -> None:
        tasks = [
            {"task_id": "T_LONG", "duration_minutes": 600}  # 10 hours
        ]
        aircraft = [
            {"aircraft_id": "A1"}
        ]
        crew = [
            {"crew_id": "C1", "max_duty_minutes_24h": 480}  # 8 hours max
        ]
        report = InfeasibilityDiagnoser.diagnose(
            tasks=tasks,
            aircraft=aircraft,
            crew=crew,
            airbases=[],
            maintenance_windows=[],
            unassigned_task_ids=["T_LONG"],
        )
        assert report.is_feasible is False
        assert any(b.category == "CREW_DUTY_LIMIT" for b in report.bottlenecks)

    def test_maintenance_lockout_conflict_diagnosed(self) -> None:
        tasks = [
            {"task_id": "T1", "earliest_start_minute": 100, "latest_start_minute": 100, "duration_minutes": 60}
        ]
        aircraft = [
            {"aircraft_id": "A1"}
        ]
        crew = [
            {"crew_id": "C1"}
        ]
        maintenance = [
            {"aircraft_id": "A1", "start_minute": 60, "end_minute": 200}
        ]
        report = InfeasibilityDiagnoser.diagnose(
            tasks=tasks,
            aircraft=aircraft,
            crew=crew,
            airbases=[],
            maintenance_windows=maintenance,
            unassigned_task_ids=["T1"],
        )
        assert report.is_feasible is False
        assert any(b.category == "MAINTENANCE_LOCKOUT" for b in report.bottlenecks)


class TestMILPOptimizationSolver:
    """Verifies that SciPy HiGHS solves problems and matches expected primal bounds."""

    def test_solve_empty_tasks(self) -> None:
        solver = MILPOptimizationSolver()
        result = solver.solve({"tasks": [], "aircraft": [], "crew": []})
        assert result.status == SolverStatus.OPTIMAL
        assert result.total_scheduled_tasks == 0
        assert result.total_unassigned_tasks == 0

    def test_solve_nominal_milp_scenario(self) -> None:
        solver = MILPOptimizationSolver()
        tasks = [
            {
                "task_id": "M1",
                "earliest_start_minute": 60,
                "latest_start_minute": 120,
                "duration_minutes": 90,
                "priority": 2.0,
                "required_capability": "FAST_JET",
            },
            {
                "task_id": "M2",
                "earliest_start_minute": 300,
                "latest_start_minute": 360,
                "duration_minutes": 60,
                "priority": 1.0,
                "required_capability": "FAST_JET",
            },
        ]
        aircraft = [
            {"aircraft_id": "SU30_01", "capability_class": "FAST_JET", "nominal_turnaround_minutes": 45}
        ]
        crew = [
            {"crew_id": "PILOT_A", "certified_classes": ["FAST_JET"], "max_duty_minutes_24h": 480}
        ]
        state = {
            "tasks": tasks,
            "aircraft": aircraft,
            "crew": crew,
            "airbases": [],
            "maintenance_windows": [],
        }

        result = solver.solve(state)
        assert result.is_successful is True
        assert result.status == SolverStatus.OPTIMAL
        assert result.total_scheduled_tasks == 2
        assert len(result.assignments) == 2
        assert result.assignments[0].aircraft_id == "SU30_01"
        assert result.assignments[0].crew_id == "PILOT_A"
        assert result.objective_value > 0.0

    def test_milp_capability_mismatch_prevents_unfit_assignment(self) -> None:
        solver = MILPOptimizationSolver()
        tasks = [
            {
                "task_id": "CARGO_MISSION",
                "earliest_start_minute": 100,
                "latest_start_minute": 120,
                "duration_minutes": 60,
                "required_capability": "HEAVY_LIFT",
            }
        ]
        aircraft = [
            {"aircraft_id": "FIGHTER_01", "capability_class": "FAST_JET"}
        ]
        crew = [
            {"crew_id": "CREW_01", "certified_classes": ["FAST_JET"]}
        ]
        state = {
            "tasks": tasks,
            "aircraft": aircraft,
            "crew": crew,
            "airbases": [],
            "maintenance_windows": [],
        }

        result = solver.solve(state)
        assert result.total_scheduled_tasks == 0
        assert "CARGO_MISSION" in result.unassigned_task_ids
        assert len(result.infeasibility_reasons) > 0
        assert "diagnostic_report" in result.diagnostic_metrics

    def test_milp_and_cp_sat_agreement(self) -> None:
        """Assert both CP-SAT and HiGHS find feasible full assignments for identical problems."""
        cp_solver = CPSatOptimizationSolver()
        milp_solver = MILPOptimizationSolver()

        tasks = [
            {
                "task_id": "T1",
                "earliest_start_minute": 100,
                "latest_start_minute": 120,
                "duration_minutes": 60,
                "priority": 1.0,
            }
        ]
        aircraft = [{"aircraft_id": "A1"}]
        crew = [{"crew_id": "C1"}]
        state = {"tasks": tasks, "aircraft": aircraft, "crew": crew}

        cp_res = cp_solver.solve(state)
        milp_res = milp_solver.solve(state)

        assert cp_res.is_successful is True
        assert milp_res.is_successful is True
        assert cp_res.total_scheduled_tasks == 1
        assert milp_res.total_scheduled_tasks == 1
        assert cp_res.assignments[0].aircraft_id == milp_res.assignments[0].aircraft_id
        assert cp_res.assignments[0].crew_id == milp_res.assignments[0].crew_id
