# AIRWISE Living Implementation Checklist & Audit Log (Phases 0 to 12)

**Project:** AIRWISE — AI-Enabled Dynamic Air Operations & Resource Optimisation  
**SIH Problem Statement:** SIH 26250  
**Document Status:** Living Master Audit Register  
**Authors & Leads:** Lakshay Bharti, Nakshatra Yadav, Nidhi Jha  

### Status Conventions
* **`NOT STARTED`**: Work has not yet begun on this task.
* **`IN PROGRESS`**: Task is actively being drafted or implemented.
* **`BLOCKED`**: Progress is halted pending resolution of a documented dependency or issue.
* **`IMPLEMENTED — NOT VERIFIED`**: Code has been written, but independent tests or verification evidence have not yet confirmed completion.
* **`VERIFIED COMPLETE`**: Code, tests, and acceptance criteria have been executed and empirically verified.

---

## Phase 0: Repository Foundations & Planning Revision

| Task ID | Description | Primary Owner | Dependencies | Status | Verification Evidence / Artifacts |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T0-01** | Inspect local filesystem and remote Git repository state | Lakshay | None | `VERIFIED COMPLETE` | Verified local folder empty, verified remote `https://github.com/DAREDEVIL-OF-NEXUS/AirOps-Optimizer` reachable via `git ls-remote`. |
| **T0-02** | Initialize local Git repository on default branch `main` | Lakshay | T0-01 | `VERIFIED COMPLETE` | Executed `git init -b main`. Local `.git` folder initialized. |
| **T0-03** | Configure Git remote origin URL | Lakshay | T0-02 | `VERIFIED COMPLETE` | Configured `origin` remote to target GitHub repo; verified with `git remote -v`. |
| **T0-04** | Create comprehensive `.gitignore` configuration | Lakshay | T0-02 | `VERIFIED COMPLETE` | Created `.gitignore` covering Python, Node, data policies, models, and virtual environments. |
| **T0-05** | Create environment configuration template `.env.example` | Lakshay | T0-04 | `VERIFIED COMPLETE` | Created `.env.example` with documented non-sensitive placeholders. |
| **T0-06** | Author master project `README.md` | Lakshay | T0-01 | `VERIFIED COMPLETE` | Master `README.md` complete with architecture topology and synthetic disclaimer. |
| **T0-07** | Author strategic milestone `ROADMAP.md` (M0–M12) | Lakshay | T0-06 | `VERIFIED COMPLETE` | Created `ROADMAP.md` covering Milestones M0 through M12. |
| **T0-08** | Author detailed operational `PHASES.md` (Phases 0–12)| Lakshay | T0-07 | `VERIFIED COMPLETE` | Created `PHASES.md` detailing all 13 implementation phases with acceptance criteria. |
| **T0-09** | Author living checklist `COMPLETION.md` | Lakshay | T0-08 | `VERIFIED COMPLETE` | Created `COMPLETION.md` tracking all granular tasks across 13 phases. |
| **T0-10** | Author technical blueprint `ARCHITECTURE.md` | Lakshay | T0-06 | `VERIFIED COMPLETE` | Authored `ARCHITECTURE.md` with 21 components, 13 Mermaid diagrams, and mathematical formulation. |
| **T0-11** | Author requirements catalog `REQUIREMENTS.md` | Lakshay | T0-06 | `VERIFIED COMPLETE` | Authored requirements catalog with stable identifiers (`FR-001`..`12`, `NFR-001`..`06`). |
| **T0-12** | Author decision log `DECISIONS.md` | Lakshay | T0-06 | `VERIFIED COMPLETE` | Authored architectural decision log documenting ADR-001 through ADR-012. |
| **T0-13** | Author team guidance `CONTRIBUTING.md` | Lakshay | T0-06 | `VERIFIED COMPLETE` | Authored `CONTRIBUTING.md` covering workflow, branch strategy, and zero-contamination policy. |
| **T0-14** | Execute Phase 0 baseline verification and initial commit | Lakshay | T0-01..13 | `VERIFIED COMPLETE` | Clean working tree verified, pushed root commit `e8509e5` to `origin/main`. |
| **T0-15** | Author external dataset audit in `docs/data-audit.md` | Nakshatra | T0-14 | `VERIFIED COMPLETE` | Audited candidates A through H; established Option B hybrid strategy and threat model. |
| **T0-16** | Author mathematical optimization design in `docs/optimisation-design.md` | Lakshay | T0-14 | `VERIFIED COMPLETE` | Detailed CP-SAT interval scheduling, decision variables, bounds, and baseline specifications. |
| **T0-17** | Author predictive modeling design in `docs/prediction-design.md` | Lakshay | T0-14 | `VERIFIED COMPLETE` | Specified $P(\text{failure})$ and $E[\text{delay}]$ targets, leakage guard, calibration, and value experiment. |
| **T0-18** | Author canonical domain model in `docs/data-model.md` | Nakshatra | T0-14 | `VERIFIED COMPLETE` | Specified all Pydantic entities, timestamps, units, and operational event envelopes. |
| **T0-19** | Author testing strategy in `docs/testing-strategy.md` | Nidhi | T0-14 | `VERIFIED COMPLETE` | Comprehensive test pyramid, domain test specs, and phase quality gates. |
| **T0-20** | Author three-person ownership in `docs/workstream-ownership.md` | All Leads | T0-14 | `VERIFIED COMPLETE` | Task matrix, effort estimation, branch strategy, and interface dependencies. |
| **T0-21** | Author dedicated ownership specifications (`Lakshay.md`, `Nakshatra.md`, `Nidhi.md`)| All Leads | T0-20 | `VERIFIED COMPLETE` | Created three individual workstream ownership specifications. |

---

## Phase 1: Dataset Discovery, Audit, and Selection

| Task ID | Description | Primary Owner | Dependencies | Status | Verification Evidence / Artifacts |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T1-01** | External dataset investigation, licensing, download verification | Nakshatra | T0-15 | `NOT STARTED` | Expected: `docs/data-audit.md` |
| **T1-02** | Implement safe ingestion loader with decompression bomb guards | Nakshatra | T1-01 | `NOT STARTED` | Expected: `src/data/safe_loader.py` |
| **T1-03** | Author safe ingestion and path traversal unit tests | Nakshatra | T1-02 | `NOT STARTED` | Expected: `tests/unit/test_safe_ingestion.py` |

---

## Phase 2: Formal Problem Definition & Mathematical Formulation

| Task ID | Description | Primary Owner | Dependencies | Status | Verification Evidence / Artifacts |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T2-01** | Formalize mathematical formulation, constraints, decision variables | Lakshay | T0-16 | `NOT STARTED` | Expected: `docs/optimisation-design.md` |
| **T2-02** | Formalize prediction targets, decision impact, and evaluation metrics | Lakshay | T2-01 | `NOT STARTED` | Expected: `docs/prediction-design.md` |

---

## Phase 3: Canonical Domain Model & Data Contracts

| Task ID | Description | Primary Owner | Dependencies | Status | Verification Evidence / Artifacts |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T3-01** | Implement Pydantic v2 domain models (`Airbase`, `Aircraft`, `Crew`) | Nakshatra | T2-01 | `NOT STARTED` | Expected: `src/domain/models.py` |
| **T3-02** | Implement validation rules and schema constraints | Nakshatra | T3-01 | `NOT STARTED` | Expected: `src/domain/schemas.py` |
| **T3-03** | Schema review & solver contract alignment | Lakshay & Nidhi | T3-01 | `NOT STARTED` | Expected: Frozen schema sign-off |
| **T3-04** | Author domain model unit tests | Nakshatra | T3-02 | `NOT STARTED` | Expected: `tests/unit/test_domain_models.py` |

---

## Phase 4: Synthetic Scenario & Event Generation

| Task ID | Description | Primary Owner | Dependencies | Status | Verification Evidence / Artifacts |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T4-01** | Build procedural scenario generator with seed-based reproducibility | Nakshatra | T3-01 | `NOT STARTED` | Expected: `src/generator/scenario_generator.py` |
| **T4-02** | Implement scenario configuration profiles (Nominal, Strained, Extreme) | Nakshatra | T4-01 | `NOT STARTED` | Expected: `src/generator/profiles.py` |
| **T4-03** | Generate small debugging fixtures and large benchmark scenarios | Nakshatra | T4-02 | `NOT STARTED` | Expected: `data/scenarios/*.json` |
| **T4-04** | Author generator determinism and referential integrity tests | Nakshatra | T4-01 | `NOT STARTED` | Expected: `tests/unit/test_generator_reproducibility.py` |

---

## Phase 5: State Management, Ingestion, Fusion, and Replay

| Task ID | Description | Primary Owner | Dependencies | Status | Verification Evidence / Artifacts |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T5-01** | Model structured operational events and immutable event envelopes | Nakshatra | T3-01 | `NOT STARTED` | Expected: `src/state/events.py` |
| **T5-02** | Implement in-memory `CanonicalOperationalState` container | Nakshatra | T5-01 | `NOT STARTED` | Expected: `src/state/canonical_state.py` |
| **T5-03** | Build Data Fusion Engine with timestamp sorting & conflict resolution | Nakshatra | T5-02 | `NOT STARTED` | Expected: `src/state/fusion_engine.py` |
| **T5-04** | Author state replay and snapshot immutability unit tests | Nakshatra | T5-03 | `NOT STARTED` | Expected: `tests/unit/test_state_replay.py` |

---

## Phase 6: Independent Feasibility Checker & Baseline Allocators

| Task ID | Description | Primary Owner | Dependencies | Status | Verification Evidence / Artifacts |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T6-01** | Implement independent `FeasibilityAuditor` for inviolable constraints | Nidhi | T3-01, T2-01 | `NOT STARTED` | Expected: `src/evaluation/auditor.py` |
| **T6-02** | Implement deterministic `GreedyBaselineSolver` (Earliest Deadline) | Nidhi | T3-01 | `NOT STARTED` | Expected: `src/baselines/greedy_solver.py` |
| **T6-03** | Author unit tests for feasibility auditing and baseline solver | Nidhi | T6-01, T6-02 | `NOT STARTED` | Expected: `tests/unit/test_baselines.py` |

---

## Phase 7: Constraint-Programming Optimiser & Solver Validation

| Task ID | Description | Primary Owner | Dependencies | Status | Verification Evidence / Artifacts |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T7-01** | Define `SolverInterface` and `OptimizationResult` data structures | Lakshay | T3-01 | `NOT STARTED` | Expected: `src/optimization/solver_interface.py` |
| **T7-02** | Implement `CPSatOptimizationSolver` with interval disjunctions | Lakshay | T7-01, T2-01 | `NOT STARTED` | Expected: `src/optimization/cp_sat_solver.py` |
| **T7-03** | Implement integer objective scaling, timeout handling, and bound extraction | Lakshay | T7-02 | `NOT STARTED` | Expected: `src/optimization/objectives.py` |
| **T7-04** | Implement optional comparative MILP solver using HiGHS | Lakshay | T7-01 | `NOT STARTED` | Expected: `src/optimization/milp_solver.py` |
| **T7-05** | Execute formal benchmark: CP-SAT vs. Greedy Baseline across 20 instances | Nidhi | T7-02, T6-02 | `NOT STARTED` | Expected: `experiments/reports/baseline_vs_cpsat.md` |

---

## Phase 8: Prediction Target Design & Reproducible Training Pipeline

| Task ID | Description | Primary Owner | Dependencies | Status | Verification Evidence / Artifacts |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T8-01** | Build feature extraction pipeline with strict timestamp guards ($t \le t_{\text{cut}}$) | Lakshay | T5-02 | `NOT STARTED` | Expected: `src/prediction/features.py` |
| **T8-02** | Establish temporal train/test split and ground truth synthetic labelers | Lakshay | T8-01 | `NOT STARTED` | Expected: `src/prediction/train.py` |
| **T8-03** | Author automated unit tests asserting zero temporal data leakage | Lakshay | T8-02 | `NOT STARTED` | Expected: `tests/unit/test_leakage_guard.py` |

---

## Phase 9: Predictive-Model Benchmarking & Selection

| Task ID | Description | Primary Owner | Dependencies | Status | Verification Evidence / Artifacts |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T9-01** | Train and calibrate LightGBM maintenance failure classifier | Lakshay | T8-02 | `NOT STARTED` | Expected: `src/prediction/models.py` |
| **T9-02** | Train turnaround delay regression model | Lakshay | T8-02 | `NOT STARTED` | Expected: `src/prediction/models.py` |
| **T9-03** | Calibrate probabilities (Platt/Isotonic); compute Brier score & log-loss | Lakshay | T9-01 | `NOT STARTED` | Expected: Calibration report & metrics |
| **T9-04** | Export pure-Python model artifacts and implement `PredictiveAnalyticsService` | Lakshay | T9-01, T9-02 | `NOT STARTED` | Expected: `src/prediction/service.py` |

---

## Phase 10: Prediction-Aware Rolling-Horizon Optimisation

| Task ID | Description | Primary Owner | Dependencies | Status | Verification Evidence / Artifacts |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T10-01**| Implement prediction-aware optimization solver (risk penalties & buffers) | Lakshay | T7-02, T9-04 | `NOT STARTED` | Expected: `src/optimization/risk_aware_solver.py` |
| **T10-02**| Execute downstream evaluation: Reactive vs. Prediction-Aware Scheduling | Nidhi | T10-01 | `NOT STARTED` | Expected: `experiments/reports/prediction_value.md` |

---

## Phase 11: What-If Simulation, Robustness, & Integrated Evaluation

| Task ID | Description | Primary Owner | Dependencies | Status | Verification Evidence / Artifacts |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T11-01**| Implement isolated `ScenarioSandbox` state cloner (zero source mutation) | Nidhi | T5-02 | `NOT STARTED` | Expected: `src/simulation/sandbox.py` |
| **T11-02**| Build disruption operators (`GroundAircraft`, `CloseRunway`, `WeatherAlert`) | Nidhi | T11-01 | `NOT STARTED` | Expected: `src/simulation/disruptions.py` |
| **T11-03**| Implement rolling-horizon replanning loop and `PlanDiffAnalyzer` | Nidhi | T11-02, T10-01 | `NOT STARTED` | Expected: `src/simulation/diff_analyzer.py` |
| **T11-04**| Execute stress testing, scalability evaluation & failure recovery tests | Nidhi | T11-03 | `NOT STARTED` | Expected: `tests/unit/test_what_if_engine.py` |

---

## Phase 12: Core API Contracts, Reproducible Release, & Frontend Handoff

| Task ID | Description | Primary Owner | Dependencies | Status | Verification Evidence / Artifacts |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T12-01**| Implement FastAPI routes for scenarios, state inspection, and events | Nakshatra | All services | `NOT STARTED` | Expected: `src/api/routes/*.py` |
| **T12-02**| Author full end-to-end integration test suite ($\ge 85\%$ coverage) | Nidhi | T12-01 | `NOT STARTED` | Expected: `tests/integration/test_api_endpoints.py` |
| **T12-03**| Author frontend integration specifications and OpenAPI export | Lakshay | T12-01 | `NOT STARTED` | Expected: `docs/FRONTEND_HANDOFF.md` |

---

## Blockers and Active Mitigations

* **Current Blockers:** None. Phase 0 planning, dataset auditing, architecture blueprinting, and workstream partitioning are 100% verified complete.
* **Next Immediate Action:** Creation of feature branches (`features/nakshatra-data-state`, `features/lakshay-optimization-ml`, `features/nidhi-validation-simulation`). Nakshatra initiates Phase 1 dataset security loaders, Lakshay initiates Phase 2 mathematical modeling reviews, and Nidhi prepares Phase 6 baseline test fixtures.
