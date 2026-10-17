"""AIRWISE Optimization Subsystem.

This package provides constraint programming and mathematical optimization
engines for dynamic multi-resource flight scheduling, asset allocation, and
counterfactual replanning.
"""

from src.optimization.cp_sat_solver import CPSatOptimizationSolver
from src.optimization.solver_config import SolverConfig
from src.optimization.solver_interface import (
    OptimizationResult,
    SolverInterface,
    SolverStatus,
    TaskAssignment,
)

__all__ = [
    "CPSatOptimizationSolver",
    "OptimizationResult",
    "SolverConfig",
    "SolverInterface",
    "SolverStatus",
    "TaskAssignment",
]
