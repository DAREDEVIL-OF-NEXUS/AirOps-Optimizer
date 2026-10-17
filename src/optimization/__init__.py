"""AIRWISE Optimization Subsystem.

This package provides constraint programming and mathematical optimization
engines for dynamic multi-resource flight scheduling, asset allocation, and
counterfactual replanning.
"""

from src.optimization.cp_sat_solver import CPSatOptimizationSolver
from src.optimization.diagnostics import (
    DiagnosticBottleneck,
    InfeasibilityDiagnoser,
    InfeasibilityReport,
)
from src.optimization.milp_solver import MILPOptimizationSolver
from src.optimization.risk_aware_solver import RiskAwareOptimizationSolver
from src.optimization.solver_config import SolverConfig
from src.optimization.solver_interface import (
    OptimizationResult,
    SolverInterface,
    SolverStatus,
    TaskAssignment,
)

__all__ = [
    "CPSatOptimizationSolver",
    "DiagnosticBottleneck",
    "InfeasibilityDiagnoser",
    "InfeasibilityReport",
    "MILPOptimizationSolver",
    "OptimizationResult",
    "RiskAwareOptimizationSolver",
    "SolverConfig",
    "SolverInterface",
    "SolverStatus",
    "TaskAssignment",
]
