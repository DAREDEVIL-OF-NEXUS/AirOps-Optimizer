# Workstream Specification: Lakshay Bharti
## Optimisation Engine, Mathematical Modeling & Predictive Analytics Core

**Role:** Senior Operations-Research Engineer & Machine-Learning Architect  
**Primary Workstream:** Optimisation & Predictive Intelligence Core  
**Associated SIH Problem Statement:** SIH 26250 (Air Power: Dynamic Air Operations & Resource Optimisation)  
**Dedicated Branch:** `features/lakshay-optimization-ml`  

---

## 1. Primary Responsibilities & Scope Boundaries

Lakshay Bharti owns the mathematical formulation, constraint programming optimization engine, predictive analytics service, and the prediction-to-optimization integration pipeline.

### Core Responsibilities:
1. **Mathematical Optimization Formulation:** Define decision variables, hard physical/regulatory constraints, soft objective penalties, and integer scaling rules.
2. **CP-SAT Solver Implementation:** Implement the primary constraint programming solver using Google OR-Tools CP-SAT via a decoupled `SolverInterface`.
3. **Solver Configuration & Robustness:** Manage time limits, search workers, optimality gap reporting, and infeasibility relaxation diagnostics.
4. **Optional MILP Comparative Model:** Implement a linearized MILP formulation (using SciPy / HiGHS) to benchmark CP-SAT against classical linear programming.
5. **Predictive Target Engineering:** Formulate and engineer feature pipelines for unscheduled maintenance failure risk ($P(\text{failure})$) and turnaround delay regression ($E[\text{delay}]$).
6. **Model Training & Calibration:** Train baseline models (Ridge, Logistic Regression) and gradient boosted trees (LightGBM); apply Platt/Isotonic probability calibration.
7. **Pure-Python Inference Service:** Export lightweight, zero-dependency model artifacts and build an inference service meeting $< 20$ms latency requirements.
8. **Prediction-Aware Optimization:** Connect calibrated risks and delay buffers directly into the solver's objective weights and interval durations.
9. **Experimental Proof of Value:** Statistically demonstrate downstream operational benefits of prediction-aware scheduling versus reactive scheduling.
10. **Test Authoring:** Author unit and property tests for optimization models, solver timeout enforcement, and ML leakage prevention.

### Explicit Scope Boundaries & Non-Goals:
- **Do NOT implement data ingestion or synthetic generators:** Consumes schemas and canonical states from Nakshatra Yadav (`src/domain/`, `src/state/`).
- **Do NOT implement the independent feasibility auditor or greedy baseline:** Nidhi Jha owns independent constraint auditing and baseline benchmarks (`src/evaluation/`, `src/baselines/`).
- **Do NOT build simulation sandboxes or diff analyzers:** Consumes simulation orchestration from Nidhi Jha (`src/simulation/`).
- **Do NOT implement frontend components:** Frontend is handled by external teammates.

---

## 2. Directory & Module Ownership

Lakshay has sole primary ownership of the following directories and files:

```
src/
├── optimization/
│   ├── __init__.py
│   ├── solver_interface.py       # Abstract solver contract
│   ├── cp_sat_solver.py          # Primary Google OR-Tools CP-SAT implementation
│   ├── objectives.py             # Objective function & integer scaling logic
│   ├── constraints.py            # Hard constraint builder (intervals, disjunctions)
│   ├── milp_solver.py            # Optional comparative MILP (HiGHS)
│   └── risk_aware_solver.py      # Solver with prediction buffer integration
├── prediction/
│   ├── __init__.py
│   ├── features.py               # Feature extraction with temporal cut-off guard
│   ├── train.py                  # Training pipeline with chronological splits
│   ├── models.py                 # LightGBM & baseline model architectures
│   └── service.py                # Pure-Python inference service
configs/
├── optimization/
│   └── solver_config.yaml        # Solver parameters, time limits, workers
└── models/
    └── model_config.yaml         # ML hyperparameters, calibration settings
tests/unit/
├── test_optimization_solver.py   # Unit tests for CP-SAT solver
├── test_solver_timeout.py        # Verification of time-limit enforcement
├── test_prediction_service.py    # Unit tests for ML inference
└── test_leakage_guard.py         # Verification of zero temporal data leakage
```

---

## 3. Public Interface Contracts

### 3.1 Input Contracts (Consumed from Nakshatra)
- Ingests `CanonicalOperationalState` from `src/state/canonical_state.py`.
- Ingests validated Pydantic domain models: `Aircraft`, `CrewMember`, `OperationalTask`, `Airbase`, `Runway` from `src/domain/models.py`.
- Ingests historical operational logs from `src/state/events.py` for ML training.

### 3.2 Output Contracts (Exposed to Nidhi & API)
```python
# src/optimization/solver_interface.py
class SolverStatus(str, Enum):
    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    MODEL_INVALID = "MODEL_INVALID"
    UNKNOWN = "UNKNOWN"

@dataclass
class TaskAssignment:
    task_id: str
    aircraft_id: str
    crew_id: str
    scheduled_start_minute: int
    scheduled_end_minute: int
    delay_minutes: int

@dataclass
class OptimizationResult:
    status: SolverStatus
    objective_value: float
    best_bound: float
    optimality_gap: float
    runtime_seconds: float
    assignments: list[TaskAssignment]
    unassigned_task_ids: list[str]
    infeasibility_reasons: list[str]

class SolverInterface(ABC):
    @abstractmethod
    def solve(self, state: CanonicalOperationalState, config: SolverConfig) -> OptimizationResult:
        pass
```

```python
# src/prediction/service.py
@dataclass
class DisruptionRiskProfile:
    aircraft_failure_probabilities: dict[str, float]  # aircraft_id -> P(fail in 24h)
    task_turnaround_delays: dict[str, float]          # task_id -> expected delay minutes

class PredictiveAnalyticsService:
    def predict_disruption_risks(
        self, state: CanonicalOperationalState, horizon_hours: float = 24.0
    ) -> DisruptionRiskProfile:
        pass
```

---

## 4. Detailed Task Breakdown & Implementation Sequence

| Phase | Task ID | Description | Prerequisites | Deliverables | Est. Days |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Phase 2** | `T2-01` | Formalize mathematical formulation, constraints, decision variables | None | `docs/optimisation-design.md` | 2.5 |
| **Phase 2** | `T2-02` | Formalize prediction targets, decision impact, and evaluation metrics | `T2-01` | `docs/prediction-design.md` | 1.5 |
| **Phase 3** | `T3-03` | Review & approve canonical domain models for optimization compatibility | Nakshatra `T3-01` | Sign-off on `src/domain/models.py` | 0.5 |
| **Phase 7** | `T7-01` | Define `SolverInterface` and `OptimizationResult` data structures | `T3-01` | `src/optimization/solver_interface.py` | 1.0 |
| **Phase 7** | `T7-02` | Implement `CPSatOptimizationSolver` with interval disjunctions & cumulative slots | `T7-01`, `T2-01` | `src/optimization/cp_sat_solver.py` | 4.0 |
| **Phase 7** | `T7-03` | Implement integer objective scaling, timeout handling, and bound extraction | `T7-02` | `src/optimization/objectives.py` | 1.5 |
| **Phase 7** | `T7-04` | Implement optional comparative MILP solver using HiGHS | `T7-01` | `src/optimization/milp_solver.py` | 2.0 |
| **Phase 8** | `T8-01` | Build feature extraction pipeline with strict timestamp guards ($t \le t_{\text{cut}}$) | Nakshatra `T5-02` | `src/prediction/features.py` | 2.5 |
| **Phase 8** | `T8-02` | Establish temporal train/test split and ground truth synthetic labelers | `T8-01` | `src/prediction/train.py` | 2.0 |
| **Phase 8** | `T8-03` | Author automated unit tests asserting zero temporal data leakage | `T8-02` | `tests/unit/test_leakage_guard.py` | 1.0 |
| **Phase 9** | `T9-01` | Train and calibrate LightGBM maintenance failure classifier | `T8-02` | `src/prediction/models.py` | 2.5 |
| **Phase 9** | `T9-02` | Train turnaround delay regression model | `T8-02` | `src/prediction/models.py` | 2.0 |
| **Phase 9** | `T9-03` | Calibrate probabilities (Platt/Isotonic); compute Brier score & log-loss | `T9-01` | Calibration report & metrics | 1.5 |
| **Phase 9** | `T9-04` | Export pure-Python model artifacts and implement `PredictiveAnalyticsService` | `T9-01`, `T9-02` | `src/prediction/service.py` | 1.5 |
| **Phase 10** | `T10-01`| Implement prediction-aware optimization solver (risk penalties & buffers) | `T7-02`, `T9-04` | `src/optimization/risk_aware_solver.py`| 2.5 |
| **Phase 12** | `T12-03`| Author frontend integration specifications and OpenAPI export | Nakshatra `T12-01` | `docs/FRONTEND_HANDOFF.md` | 1.5 |

**Total Estimated Workload:** 22.0 Engineering Days (55 Story Points).

---

## 5. Testing & Quality Acceptance Criteria

1. **Solver Feasibility:** The CP-SAT solver must produce schedules with **zero** overlapping aircraft assignments, zero crew duty-hour violations, and zero qualification mismatches.
2. **Baseline Superiority:** On 20 standardized benchmark scenarios, CP-SAT must match or exceed the objective value of Nidhi's Greedy Baseline in 100% of cases.
3. **Timeout Compliance:** The solver must terminate cleanly and return the best-found primal solution within `time_limit_seconds ± 0.5s`.
4. **Predictive Performance:** LightGBM classifier must achieve $\text{ROC-AUC} \ge 0.75$ and Brier score $\le 0.15$ on held-out temporal test splits, outperforming the linear baseline by $\ge 15\%$.
5. **Zero Data Leakage:** `tests/unit/test_leakage_guard.py` must pass with zero future timestamp observations in training feature matrices.

---

## 6. Deferred Planning Workflow (Mandatory Instruction)

> [!IMPORTANT]
> When Lakshay's coding agent begins implementation:
> 1. Read `ARCHITECTURE.md`, `PHASES.md`, `ROADMAP.md`, `REQUIREMENTS.md`, and this document (`Lakshay.md`).
> 2. Create `PHASES_LAKSHAY.md` detailing granular implementation sub-phases.
> 3. Create `CHECKLIST_LAKSHAY.md` tracking daily task completion with commit hashes.
> 4. Do not modify files outside `src/optimization/`, `src/prediction/`, and owned test directories.
