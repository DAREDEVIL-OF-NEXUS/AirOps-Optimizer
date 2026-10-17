"""Unit Tests for Optimization Solver Interface and Configuration.

Verifies TaskAssignment invariants, OptimizationResult serialization,
SolverConfig bounds checking, and YAML configuration loading.
"""

from pathlib import Path

import pytest

from src.optimization.solver_config import SolverConfig
from src.optimization.solver_interface import (
    OptimizationResult,
    SolverInterface,
    SolverStatus,
    TaskAssignment,
)


class TestSolverStatus:
    """Test suite for SolverStatus enumeration."""

    def test_status_values(self) -> None:
        assert SolverStatus.OPTIMAL.value == "OPTIMAL"
        assert SolverStatus.FEASIBLE.value == "FEASIBLE"
        assert SolverStatus.INFEASIBLE.value == "INFEASIBLE"
        assert SolverStatus.MODEL_INVALID.value == "MODEL_INVALID"
        assert SolverStatus.UNKNOWN.value == "UNKNOWN"

    def test_status_from_string(self) -> None:
        assert SolverStatus("OPTIMAL") == SolverStatus.OPTIMAL
        assert SolverStatus("FEASIBLE") == SolverStatus.FEASIBLE


class TestTaskAssignment:
    """Test suite for TaskAssignment dataclass."""

    def test_valid_assignment_creation(self) -> None:
        assignment = TaskAssignment(
            task_id="TASK-001",
            aircraft_id="AC-101",
            crew_id="CREW-05",
            scheduled_start_minute=60,
            scheduled_end_minute=180,
            delay_minutes=10,
            turnaround_buffer_minutes=45,
            metadata={"priority": 100},
        )
        assert assignment.task_id == "TASK-001"
        assert assignment.aircraft_id == "AC-101"
        assert assignment.crew_id == "CREW-05"
        assert assignment.scheduled_start_minute == 60
        assert assignment.scheduled_end_minute == 180
        assert assignment.duration_minutes == 120
        assert assignment.delay_minutes == 10
        assert assignment.metadata["priority"] == 100

    def test_invalid_inverted_end_time_raises_error(self) -> None:
        with pytest.raises(ValueError, match="cannot be earlier than scheduled_start_minute"):
            TaskAssignment(
                task_id="TASK-002",
                aircraft_id="AC-101",
                crew_id="CREW-01",
                scheduled_start_minute=200,
                scheduled_end_minute=100,
            )

    def test_negative_delay_raises_error(self) -> None:
        with pytest.raises(ValueError, match="must be non-negative"):
            TaskAssignment(
                task_id="TASK-003",
                aircraft_id="AC-101",
                crew_id="CREW-01",
                scheduled_start_minute=100,
                scheduled_end_minute=200,
                delay_minutes=-5,
            )

    def test_to_dict_serialization(self) -> None:
        assignment = TaskAssignment(
            task_id="TASK-004",
            aircraft_id="AC-102",
            crew_id="CREW-02",
            scheduled_start_minute=50,
            scheduled_end_minute=110,
        )
        data = assignment.to_dict()
        assert isinstance(data, dict)
        assert data["task_id"] == "TASK-004"
        assert data["duration_minutes"] == 60 or "duration_minutes" not in data
        assert data["scheduled_start_minute"] == 50


class TestOptimizationResult:
    """Test suite for OptimizationResult envelope."""

    def test_result_properties(self) -> None:
        assignment1 = TaskAssignment(
            task_id="T1", aircraft_id="A1", crew_id="C1", scheduled_start_minute=0, scheduled_end_minute=60
        )
        assignment2 = TaskAssignment(
            task_id="T2", aircraft_id="A2", crew_id="C2", scheduled_start_minute=60, scheduled_end_minute=120
        )
        result = OptimizationResult(
            status=SolverStatus.OPTIMAL,
            objective_value=15000.0,
            best_bound=15000.0,
            optimality_gap=0.0,
            runtime_seconds=1.25,
            assignments=[assignment1, assignment2],
            unassigned_task_ids=["T3"],
            infeasibility_reasons=[],
            solver_name="TestSolver",
            diagnostic_metrics={"nodes": 100},
        )
        assert result.is_successful is True
        assert result.total_scheduled_tasks == 2
        assert result.total_unassigned_tasks == 1
        assert result.get_assignment_for_task("T1") == assignment1
        assert result.get_assignment_for_task("T3") is None

    def test_unsuccessful_result(self) -> None:
        result = OptimizationResult(
            status=SolverStatus.INFEASIBLE,
            infeasibility_reasons=["Crew duty-hour limits breached."],
        )
        assert result.is_successful is False
        assert result.total_scheduled_tasks == 0
        assert len(result.infeasibility_reasons) == 1

    def test_serialization_roundtrip(self) -> None:
        assignment = TaskAssignment(
            task_id="TASK-A",
            aircraft_id="AC-01",
            crew_id="CR-01",
            scheduled_start_minute=10,
            scheduled_end_minute=70,
            delay_minutes=5,
        )
        original = OptimizationResult(
            status=SolverStatus.FEASIBLE,
            objective_value=9800.5,
            best_bound=10200.0,
            optimality_gap=0.04,
            runtime_seconds=0.45,
            assignments=[assignment],
            unassigned_task_ids=["TASK-B"],
            infeasibility_reasons=["Runway congestion"],
            solver_name="CP_SAT",
            diagnostic_metrics={"branches": 450},
        )
        data = original.to_dict()
        reconstituted = OptimizationResult.from_dict(data)

        assert reconstituted.status == SolverStatus.FEASIBLE
        assert reconstituted.objective_value == 9800.5
        assert reconstituted.total_scheduled_tasks == 1
        assert reconstituted.assignments[0].task_id == "TASK-A"
        assert reconstituted.assignments[0].aircraft_id == "AC-01"
        assert reconstituted.unassigned_task_ids == ["TASK-B"]
        assert reconstituted.diagnostic_metrics["branches"] == 450


class TestSolverConfig:
    """Test suite for SolverConfig parameters and YAML loading."""

    def test_default_config_validity(self) -> None:
        config = SolverConfig()
        assert config.solver_type == "OR_TOOLS_CP_SAT"
        assert config.time_limit_seconds == 30.0
        assert config.num_search_workers == 8
        assert config.integer_scaling_factor == 10000
        assert config.weight_priority == 1000

    def test_invalid_timeout_raises_error(self) -> None:
        with pytest.raises(ValueError, match="time_limit_seconds must be positive"):
            SolverConfig(time_limit_seconds=0.0)

    def test_invalid_workers_raises_error(self) -> None:
        with pytest.raises(ValueError, match="num_search_workers must be at least 1"):
            SolverConfig(num_search_workers=0)

    def test_negative_weight_raises_error(self) -> None:
        with pytest.raises(ValueError, match="Objective weights cannot be negative"):
            SolverConfig(weight_priority=-10)

    def test_yaml_serialization_and_deserialization(self, tmp_path: Path) -> None:
        config = SolverConfig(
            solver_type="GREEDY_BASELINE",
            time_limit_seconds=15.0,
            num_search_workers=4,
            weight_priority=500,
        )
        yaml_path = tmp_path / "test_solver_config.yaml"
        config.to_yaml(yaml_path)

        assert yaml_path.exists()
        loaded = SolverConfig.from_yaml(yaml_path)
        assert loaded.solver_type == "GREEDY_BASELINE"
        assert loaded.time_limit_seconds == 15.0
        assert loaded.num_search_workers == 4
        assert loaded.weight_priority == 500

    def test_load_default_template_file(self) -> None:
        repo_template = Path("configs/optimization/solver_config.yaml")
        assert repo_template.exists(), "Default configuration template must exist."
        config = SolverConfig.from_yaml(repo_template)
        assert config.solver_type == "OR_TOOLS_CP_SAT"
        assert config.time_limit_seconds == 30.0


class TestSolverInterfaceContract:
    """Test suite for abstract SolverInterface."""

    def test_abstract_class_cannot_be_instantiated(self) -> None:
        with pytest.raises(TypeError):
            SolverInterface()  # type: ignore[abstract]

    def test_concrete_implementation(self) -> None:
        class DummySolver(SolverInterface):
            def solve(self, state: object, config: SolverConfig) -> OptimizationResult:
                return OptimizationResult(status=SolverStatus.FEASIBLE)

        solver = DummySolver()
        result = solver.solve(state=None, config=SolverConfig())
        assert result.status == SolverStatus.FEASIBLE
