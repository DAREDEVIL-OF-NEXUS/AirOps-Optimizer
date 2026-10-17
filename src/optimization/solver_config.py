"""Solver Configuration Model and YAML Loader.

This module manages all runtime hyperparameters, search limits, multi-threaded
worker allocation, integer scaling constants, and objective penalty weights
for the optimization engines.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SolverConfig:
    """Configuration parameters and weights for optimization solvers.

    Attributes:
        solver_type: Identifier of solver algorithm ("OR_TOOLS_CP_SAT", "GREEDY_BASELINE", "MILP_HIGHS").
        time_limit_seconds: Maximum wall-clock seconds allocated for optimization search.
        num_search_workers: Number of parallel CPU worker threads (for CP-SAT / MILP).
        log_search_progress: True if solver should stream search iterations to stdout/logs.
        random_seed: Random seed for deterministic tie-breaking.
        integer_scaling_factor: Scale multiplier for floating-point probabilities (e.g. 10,000).
        weight_priority: Multiplier reward for completing tasks based on priority ($w_t$).
        weight_delay_minute: Penalty per minute of departure delay beyond earliest start.
        weight_risk: Penalty weight for assigning high-failure-risk airframes to sorties.
        weight_churn: Penalty weight per schedule reassignment in counterfactual replanning.
        allow_partial_fulfillments: True if solver may leave low-priority tasks unassigned when constrained.
    """

    solver_type: str = "OR_TOOLS_CP_SAT"
    time_limit_seconds: float = 30.0
    num_search_workers: int = 8
    log_search_progress: bool = False
    random_seed: int = 42
    integer_scaling_factor: int = 10000
    weight_priority: int = 1000
    weight_delay_minute: int = 10
    weight_risk: int = 500
    weight_churn: int = 250
    allow_partial_fulfillments: bool = True

    def __post_init__(self) -> None:
        if self.time_limit_seconds <= 0.0:
            raise ValueError(f"time_limit_seconds must be positive, got {self.time_limit_seconds}")
        if self.num_search_workers < 1:
            raise ValueError(f"num_search_workers must be at least 1, got {self.num_search_workers}")
        if self.integer_scaling_factor < 100:
            raise ValueError("integer_scaling_factor must be at least 100 to preserve precision.")
        if self.weight_priority < 0 or self.weight_delay_minute < 0:
            raise ValueError("Objective weights cannot be negative.")

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary representation."""
        return asdict(self)

    def to_yaml(self, path: Path | str | None = None) -> str:
        """Serialize configuration to a YAML string or write to file."""
        content = yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)
        if path:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        return content

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SolverConfig:
        """Construct SolverConfig from dictionary with validation."""
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    @classmethod
    def from_yaml(cls, path_or_stream: Path | str) -> SolverConfig:
        """Load SolverConfig from a YAML file path or stream string."""
        path = Path(path_or_stream) if isinstance(path_or_stream, (str, Path)) and Path(str(path_or_stream)).exists() else None
        if path and path.is_file():
            text = path.read_text(encoding="utf-8")
        else:
            text = str(path_or_stream)
        data = yaml.safe_load(text) or {}
        return cls.from_dict(data)
