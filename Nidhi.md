# Workstream Specification: Nidhi Jha
## Independent Validation, Baseline Comparison, Simulation & Scientific Evaluation

**Role:** Senior Test Architect & Operations-Research Evaluation Lead  
**Primary Workstream:** Independent Feasibility, Baseline Benchmarks, What-If Simulation & Evaluation  
**Associated SIH Problem Statement:** SIH 26250 (Air Power: Dynamic Air Operations & Resource Optimisation)  
**Dedicated Branch:** `features/nidhi-validation-simulation`  

---

## 1. Primary Responsibilities & Scope Boundaries

Nidhi Jha owns independent quality verification, comparative baseline heuristics, counterfactual what-if simulation, rolling-horizon replanning orchestration, and empirical benchmark evaluations.

### Core Responsibilities:
1. **Independent Feasibility Auditor:** Implement an independent verification module that audits candidate schedules against all hard physical/regulatory constraints without relying on solver variables.
2. **Transparent Greedy Baseline Solver:** Implement a deterministic Earliest-Deadline-First greedy allocator to serve as a strict, non-vacuous benchmark against the CP-SAT solver.
3. **Solver Benchmarking Framework:** Define standardized benchmark harnesses comparing runtime, objective value, unfulfilled tasks, and optimality gaps between CP-SAT and the Greedy baseline.
4. **Counterfactual What-If Sandbox:** Implement the isolated state cloning engine allowing operators to inject hypothetical disruptions without mutating the original operational plan.
5. **Disruption Injection Operators:** Build operational mutation operators: `GroundAircraft`, `CloseRunway`, `WeatherDegradation`, `TaskDelay`.
6. **Plan Differential Analyzer:** Implement the schedule diffing engine measuring reassignments, net delay variance, cancelled flight legs, and churn penalties.
7. **Rolling-Horizon Replanning Orchestration:** Build the dynamic replanning loop, consuming Lakshay's solver and prediction interfaces to simulate operational day execution.
8. **Robustness & Scalability Experiments:** Execute parametric sweeps across scenario scales (10 to 500 tasks) and disruption severities; record statistical confidence intervals.
9. **Full Integration Testing:** Own end-to-end integration tests (`tests/integration/`) verifying API endpoints and system-wide workflows.
10. **Scientific Evaluation Report:** Author publication-grade empirical reports and Pareto trade-off analyses documenting solver and prediction performance.

### Explicit Scope Boundaries & Non-Goals:
- **Do NOT implement a competing CP-SAT solver:** Lakshay owns the CP-SAT and MILP optimization models (`src/optimization/`). Nidhi evaluates them independently.
- **Do NOT train duplicate ML models:** Lakshay owns predictive feature engineering and model training (`src/prediction/`).
- **Do NOT implement data ingestion or procedural generation:** Nakshatra owns schemas, generators, and canonical state management (`src/domain/`, `src/state/`).
- **Do NOT build frontend UI components:** Frontend is handled by external teammates.

---

## 2. Directory & Module Ownership

Nidhi has sole primary ownership of the following directories and files:

```
src/
├── baselines/
│   ├── __init__.py
│   └── greedy_solver.py          # Deterministic Earliest-Deadline-First heuristic
├── evaluation/
│   ├── __init__.py
│   ├── auditor.py                # Independent constraint feasibility auditor
│   ├── metrics.py                # KPI calculations (Readiness, Churn, Delays)
│   └── statistical_tests.py      # Paired t-tests, Wilcoxon tests, confidence intervals
├── simulation/
│   ├── __init__.py
│   ├── sandbox.py                # Isolated state cloner (0 mutation on baseline)
│   ├── disruptions.py            # Disruption operators (Grounding, Closure, Weather)
│   ├── what_if_engine.py         # Dynamic re-optimization orchestrator
│   └── diff_analyzer.py          # Structured plan diff & ripple impact engine
experiments/
├── benchmark_runner.py           # Automated headless experiment harness
├── configs/                      # Experiment parameter matrices
├── reports/
│   └── EVALUATION_REPORT.md      # Comprehensive scientific findings and charts
│   └── results/                  # JSON/CSV benchmark run artifacts
tests/integration/
├── test_api_endpoints.py         # End-to-end FastAPI integration tests
├── test_end_to_end_replanning.py # Full lifecycle: State -> Solve -> Disrupt -> Replan
└── test_frontend_contracts.py    # Verification of frontend contract compatibility
```

---

## 3. Public Interface Contracts

### 3.1 Provided Contracts (Exposed to API & Benchmark Harness)
```python
# src/evaluation/auditor.py
@dataclass
class AuditViolation:
    constraint_name: str
    entity_id: str
    timestamp_minute: int
    details: str

@dataclass
class AuditReport:
    is_feasible: bool
    total_violations: int
    violations: list[AuditViolation]
    audited_objective_value: float

class FeasibilityAuditor:
    def audit(
        self,
        state: CanonicalOperationalState,
        plan: OptimizationResult,
    ) -> AuditReport:
        """Independently audit an optimization result against all domain constraints."""
        ...
```

```python
# src/simulation/diff_analyzer.py
@dataclass
class PlanDelta:
    reassigned_tasks: list[dict[str, str]]  # task_id, original_asset, new_asset
    newly_unassigned_tasks: list[str]
    delay_variance_minutes: int
    crew_overtime_shift_minutes: int
    total_churn_penalty: float

class PlanDiffAnalyzer:
    def compute_diff(
        self,
        original_plan: OptimizationResult,
        revised_plan: OptimizationResult,
    ) -> PlanDelta:
        """Compute structured differential analysis between two operational plans."""
        ...
```

---

## 4. Detailed Task Breakdown & Implementation Sequence

| Phase | Task ID | Description | Prerequisites | Deliverables | Est. Days |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Phase 6** | `T6-01` | Implement independent `FeasibilityAuditor` for inviolable constraints | Nakshatra `T3-01`, Lakshay `T2-01` | `src/evaluation/auditor.py` | 3.0 |
| **Phase 6** | `T6-02` | Implement deterministic `GreedyBaselineSolver` (Earliest Deadline First) | Nakshatra `T3-01` | `src/baselines/greedy_solver.py` | 2.5 |
| **Phase 6** | `T6-03` | Author unit tests for feasibility auditing and baseline solver | `T6-01`, `T6-02` | `tests/unit/test_baselines.py` | 1.5 |
| **Phase 7** | `T7-05` | Execute formal benchmark: CP-SAT vs. Greedy Baseline across 20 instances | Lakshay `T7-02`, `T6-02` | `experiments/reports/baseline_vs_cpsat.md` | 1.5 |
| **Phase 10** | `T10-02`| Execute downstream evaluation: Reactive vs. Prediction-Aware Scheduling | Lakshay `T10-01` | `experiments/reports/prediction_value.md` | 2.5 |
| **Phase 11** | `T11-01`| Implement isolated `ScenarioSandbox` state cloner (zero source mutation) | Nakshatra `T5-02` | `src/simulation/sandbox.py` | 2.0 |
| **Phase 11** | `T11-02`| Build disruption operators (`GroundAircraft`, `CloseRunway`, `WeatherAlert`) | `T11-01` | `src/simulation/disruptions.py` | 2.0 |
| **Phase 11** | `T11-03`| Implement rolling-horizon replanning loop and `PlanDiffAnalyzer` | `T11-02`, Lakshay `T10-01` | `src/simulation/diff_analyzer.py` | 2.5 |
| **Phase 11** | `T11-04`| Execute stress testing, scalability evaluation & failure recovery tests | `T11-03` | `tests/unit/test_what_if_engine.py` | 2.0 |
| **Phase 12** | `T12-02`| Author full end-to-end integration test suite ($\ge 85\%$ coverage) | All services | `tests/integration/test_api_endpoints.py` | 2.0 |

**Total Estimated Workload:** 21.5 Engineering Days (53 Story Points).

---

## 5. Testing & Quality Acceptance Criteria

1. **Independent Verification Integrity:** `FeasibilityAuditor` must accurately flag injected constraint violations (overlapping sorties, unqualified pilots, duty-hour breaches) with 100% precision and recall.
2. **Sandbox Isolation:** Modifying or re-optimizing a cloned scenario in `ScenarioSandbox` must cause **zero** byte modifications to the baseline scenario in memory or database.
3. **Plan Diff Accuracy:** `PlanDiffAnalyzer` must correctly quantify every reassignment, delay shift, and cancelled sortie without missing ripple effects.
4. **Reproducibility of Experiments:** All benchmark scripts in `experiments/` must run headlessly and reproduce identical results when provided with documented seeds.
5. **Statistical Rigor:** Comparative evaluations between CP-SAT and baselines must report mean, standard deviation, and paired p-values ($p < 0.01$).

---

## 6. Deferred Planning Workflow (Mandatory Instruction)

> [!IMPORTANT]
> When Nidhi's coding agent begins implementation:
> 1. Read `ARCHITECTURE.md`, `PHASES.md`, `ROADMAP.md`, `REQUIREMENTS.md`, and this document (`Nidhi.md`).
> 2. Create `PHASES_NIDHI.md` detailing granular implementation sub-phases.
> 3. Create `CHECKLIST_NIDHI.md` tracking daily task completion with commit hashes.
> 4. Do not modify files outside `src/baselines/`, `src/evaluation/`, `src/simulation/`, `experiments/`, and integration test directories.
