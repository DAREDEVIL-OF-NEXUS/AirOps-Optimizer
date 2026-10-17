# AIRWISE Master Implementation Phases (Phases 0 to 12)

**Project:** AIRWISE — AI-Enabled Dynamic Air Operations & Resource Optimisation  
**SIH Problem Statement:** SIH 26250  
**Document Status:** Complete & Frozen Implementation Specification  
**Authors:** Lakshay Bharti, Nakshatra Yadav, Nidhi Jha  

---

## Phase 0: Repository Foundations & Planning Revision

* **Phase Identifier:** `PHASE-0`
* **Objective:** Establish the development environment, Git hygiene, project governance, comprehensive architectural blueprints, dataset research, and three-person workstream partitioning.
* **Scope:** Repository configuration, directory scaffolding, `.gitignore`, `.env.example`, architectural blueprints, ADRs, requirements traceability, dataset audit, and workstream ownership documents (`Lakshay.md`, `Nakshatra.md`, `Nidhi.md`).
* **Prerequisites:** Clean repository initialized on `main` branch.
* **Input & Output Contracts:** In: Master initialization prompt. Out: Complete documentation suite and clean Git tree.
* **Files / Modules Owned:** Root documentation (`README.md`, `ARCHITECTURE.md`, `PHASES.md`, `ROADMAP.md`, `COMPLETION.md`, `REQUIREMENTS.md`, `DECISIONS.md`, `CONTRIBUTING.md`, `Lakshay.md`, `Nakshatra.md`, `Nidhi.md`, `docs/*`).
* **Deliverables:** Complete project documentation suite, clean Git commit, clean working tree.
* **Tests & Validation:** Markdown link validation, Git status check, remote synchronization check.
* **Acceptance Criteria:**
  - All documentation files present, substantive, internally consistent, and cross-referenced.
  - Three-person workstream partition is mutually exclusive and collectively exhaustive.
  - Remote repository synchronized with zero unreviewed artifacts.
* **Definition of Done:** Documentation verified and committed to `main`.
* **Explicit Non-Goals:** Writing application code, running solvers, training models, or developing frontend code.
* **Workstream Ownership:** All three leads (Lakshay Lead).
* **Execution Mode:** Collaborative planning; completed before parallel branching.

---

## Phase 1: Dataset Discovery, Audit, and Selection

* **Phase Identifier:** `PHASE-1`
* **Objective:** Investigate external candidate datasets (TU Delft, NASA C-MAPSS, US BTS, ROADEF, Roboflow), assess licensing, access, schema compatibility, and security vulnerabilities, delivering a formal dataset decision report.
* **Scope:** Audit candidates A through H, threat modeling, safe ingestion checklist, download verification.
* **Prerequisites:** `PHASE-0` verified complete.
* **Input & Output Contracts:** In: Public research portals. Out: `docs/data-audit.md` and safe ingestion adapters in `src/data/`.
* **Files / Modules Owned:** `docs/data-audit.md`, `src/data/adapters.py`, `src/data/safe_loader.py`, `tests/unit/test_safe_ingestion.py`.
* **Deliverables:** Formal dataset audit report, safe ingestion loader with decompression bomb guards, SHA-256 checksums.
* **Tests & Validation:** Unit tests asserting rejection of archives $> 50$MB and Zip-Slip path traversals (`tests/unit/test_safe_ingestion.py`).
* **Acceptance Criteria:**
  - Audit document complete with all 15 required fields per candidate.
  - Formal hybrid selection decision documented (Option B).
  - Security threat model and safe handling rules verified.
* **Definition of Done:** `docs/data-audit.md` approved, safe ingestion tests pass.
* **Explicit Non-Goals:** Committing large bulk datasets (> 50 MB) to Git.
* **Workstream Ownership:** Nakshatra Yadav.
* **Execution Mode:** Independent workstream task on `features/nakshatra-data-state`.

---

## Phase 2: Formal Problem Definition & Mathematical Formulation

* **Phase Identifier:** `PHASE-2`
* **Objective:** Define the formal mathematical optimization formulation and decision-relevant prediction targets before writing solver code.
* **Scope:** Decision variables, hard physical/regulatory constraints, soft objective penalty terms, integer scaling rules, candidate prediction target formulas, and decision value mapping.
* **Prerequisites:** `PHASE-0` verified complete.
* **Input & Output Contracts:** In: Problem requirements. Out: `docs/optimisation-design.md` and `docs/prediction-design.md`.
* **Files / Modules Owned:** `docs/optimisation-design.md`, `docs/prediction-design.md`.
* **Deliverables:** Complete mathematical optimization specification and predictive modeling design documents.
* **Tests & Validation:** Mathematical boundary review, variable integer scaling verification, coefficient overflow checks.
* **Acceptance Criteria:**
  - All decision variables, indices, constraints, and objective terms mathematically defined.
  - Prediction targets ($P(\text{failure})$, $E[\text{delay}]$) mapped to concrete optimization inputs (penalty, buffers).
  - Integer scaling policy for CP-SAT formulated and verified against 64-bit bounds.
* **Definition of Done:** Both design documents reviewed and approved by all leads.
* **Explicit Non-Goals:** Implementing OR-Tools solver code or training models.
* **Workstream Ownership:** Lakshay Bharti.
* **Execution Mode:** Independent workstream task on `features/lakshay-optimization-ml`.

---

## Phase 3: Canonical Domain Model & Data Contracts

* **Phase Identifier:** `PHASE-3`
* **Objective:** Implement strongly-typed, immutable Pydantic v2 domain models and data contracts for all operational entities and events.
* **Scope:** Entities (`Airbase`, `Runway`, `AirframeType`, `Aircraft`, `CrewMember`, `OperationalTask`, `WeatherWindow`), units, timestamp normalization, and schema validation rules.
* **Prerequisites:** `PHASE-1` and `PHASE-2` completed.
* **Input & Output Contracts:** In: Mathematical entity definitions. Out: `src/domain/models.py`, `schemas.py`, `docs/data-model.md`.
* **Files / Modules Owned:** `src/domain/enums.py`, `src/domain/models.py`, `src/domain/schemas.py`, `docs/data-model.md`, `tests/unit/test_domain_models.py`.
* **Deliverables:** Pydantic v2 domain schemas, domain model documentation, 100% passing schema unit tests.
* **Tests & Validation:** `pytest tests/unit/test_domain_models.py` verifying bounds, regex patterns, and invalid input rejections.
* **Acceptance Criteria:**
  - 100% validation coverage across all entities.
  - Zero un-typed fields; explicit units on all physical metrics.
  - Frozen schemas reviewed and signed off by Lakshay and Nidhi.
* **Definition of Done:** Schemas frozen and merged to feature branches.
* **Explicit Non-Goals:** Database ORM mapping or procedural generation.
* **Workstream Ownership:** Nakshatra Yadav (Co-review by Lakshay & Nidhi).
* **Execution Mode:** Foundational shared interface; must be frozen before Phase 4, 6, and 7.

---

## Phase 4: Synthetic Scenario & Event Generation

* **Phase Identifier:** `PHASE-4`
* **Objective:** Design and implement a deterministic, configurable procedural scenario generator producing self-consistent operational scenarios with ground truth.
* **Scope:** Generator engine, seed control, scale configurations (10 to 500 tasks), strain parameters, and reference debugging fixtures.
* **Prerequisites:** `PHASE-3` verified complete.
* **Input & Output Contracts:** In: `GeneratorConfig`. Out: Canonical scenario JSON files and fixtures.
* **Files / Modules Owned:** `src/generator/scenario_generator.py`, `src/generator/profiles.py`, `data/scenarios/`, `tests/unit/test_generator_reproducibility.py`.
* **Deliverables:** Procedural generator engine, pre-generated demo scenarios, reproducible unit tests.
* **Tests & Validation:**
  - Seed determinism test: two runs with `seed=42` produce byte-identical JSON.
  - Referential integrity assertion: 0 dangling foreign keys across 1,000 generated entities.
* **Acceptance Criteria:**
  - Generates 100-task scenario in $< 1.0$s on standard CPU.
  - Zero schema validation errors on generated scenario output.
* **Definition of Done:** Generator passes all reproducibility and integrity tests.
* **Explicit Non-Goals:** Generating real-world military tactical targeting data.
* **Workstream Ownership:** Nakshatra Yadav.
* **Execution Mode:** Independent workstream task on `features/nakshatra-data-state`.

---

## Phase 5: State Management, Ingestion, Fusion, and Replay

* **Phase Identifier:** `PHASE-5`
* **Objective:** Implement the in-memory `CanonicalOperationalState` container, operational event catalog, snapshotting engine, and deterministic event replay fusion engine.
* **Scope:** Structured event schemas (`AircraftGrounded`, `RunwayClosed`), thread-safe state container, out-of-order event sorting, and snapshot rollback.
* **Prerequisites:** `PHASE-3` and `PHASE-4` completed.
* **Input & Output Contracts:** In: Operational events and scenario states. Out: Queryable canonical state and snapshots.
* **Files / Modules Owned:** `src/state/canonical_state.py`, `src/state/events.py`, `src/state/fusion_engine.py`, `tests/unit/test_state_replay.py`.
* **Deliverables:** In-memory state container, event catalog, fusion engine, state transition test suite.
* **Tests & Validation:** `pytest tests/unit/test_state_replay.py` asserting that out-of-order event replay produces identical state hashes to chronological replay.
* **Acceptance Criteria:**
  - Sub-millisecond ($< 1$ms) entity lookups by identifier.
  - State snapshotting completes in $< 5$ms for 500 entities.
* **Definition of Done:** Fusion engine deterministic and verified across 10 test event sequences.
* **Explicit Non-Goals:** External message broker (Kafka/RabbitMQ) infrastructure.
* **Workstream Ownership:** Nakshatra Yadav.
* **Execution Mode:** Independent workstream task on `features/nakshatra-data-state`.

---

## Phase 6: Independent Feasibility Checker & Baseline Allocators

* **Phase Identifier:** `PHASE-6`
* **Objective:** Implement the independent constraint feasibility auditor and a transparent deterministic Greedy Baseline allocator.
* **Scope:** Independent constraint auditing without relying on solver variables, Earliest-Deadline-First greedy allocator, and baseline test suite.
* **Prerequisites:** `PHASE-3` and `PHASE-4` completed.
* **Input & Output Contracts:** In: Canonical state and candidate plans. Out: `AuditReport` and baseline `OptimizationResult`.
* **Files / Modules Owned:** `src/evaluation/auditor.py`, `src/baselines/greedy_solver.py`, `src/evaluation/metrics.py`, `tests/unit/test_baselines.py`.
* **Deliverables:** `FeasibilityAuditor`, `GreedyBaselineSolver`, metrics calculation engine, baseline test suite.
* **Tests & Validation:**
  - Audit tests: Assert injected overlapping sorties or unqualified crew are flagged with 100% precision.
  - Greedy solver tests: Verify greedy solver produces a feasible schedule on synthetic fixtures in $< 50$ms.
* **Acceptance Criteria:**
  - Auditor operates strictly on external interval arithmetic without solver internals.
  - Greedy baseline executes deterministically and provides honest benchmark.
* **Definition of Done:** Auditor and Greedy solver pass all unit tests on synthetic fixtures.
* **Explicit Non-Goals:** Implementing the CP-SAT solver.
* **Workstream Ownership:** Nidhi Jha.
* **Execution Mode:** Independent workstream task on `features/nidhi-validation-simulation`.

---

## Phase 7: Constraint-Programming Optimiser & Solver Validation

* **Phase Identifier:** `PHASE-7`
* **Objective:** Implement the primary constraint programming solver using Google OR-Tools CP-SAT, integer objective scaling, timeout handling, and comparative benchmarking against the Greedy baseline.
* **Scope:** `SolverInterface`, `CPSatOptimizationSolver`, interval disjunction constraints, cumulative runway capacity, integer scaling, optional MILP comparative model, and benchmark comparison.
* **Prerequisites:** `PHASE-2`, `PHASE-3`, `PHASE-5`, and `PHASE-6` completed.
* **Input & Output Contracts:** In: Canonical state and `SolverConfig`. Out: `OptimizationResult`.
* **Files / Modules Owned:** `src/optimization/solver_interface.py`, `src/optimization/cp_sat_solver.py`, `src/optimization/constraints.py`, `src/optimization/objectives.py`, `src/optimization/milp_solver.py`, `tests/unit/test_optimization_solver.py`.
* **Deliverables:** CP-SAT solver implementation, optional MILP solver, benchmark report comparing CP-SAT vs Greedy.
* **Tests & Validation:**
  - `pytest tests/unit/test_optimization_solver.py`
  - Run CP-SAT and Greedy on 20 identical scenarios; assert CP-SAT objective $\ge$ Greedy in 100% of cases and zero hard constraint violations confirmed by Nidhi's `FeasibilityAuditor`.
* **Acceptance Criteria:**
  - Zero constraint violations on all feasible test scenarios.
  - Clean termination within `time_limit_seconds ± 0.5s`.
* **Definition of Done:** Solver passes all feasibility audits and comparative benchmarks.
* **Explicit Non-Goals:** Deep reinforcement learning or heuristic approximations.
* **Workstream Ownership:** Lakshay Bharti (Benchmarking execution by Nidhi Jha).
* **Execution Mode:** Collaborative integration between Lakshay and Nidhi.

---

## Phase 8: Prediction Target Design & Reproducible Training Pipeline

* **Phase Identifier:** `PHASE-8`
* **Objective:** Build feature engineering pipelines, chronological train/test splits, and synthetic ground-truth labeling without data leakage.
* **Scope:** Feature extraction from state histories, timestamp cutoff guards ($t \le t_{\text{cut}}$), temporal partitioning, and automated leakage tests.
* **Prerequisites:** `PHASE-4` and `PHASE-5` completed.
* **Input & Output Contracts:** In: Canonical states and event logs. Out: Feature matrices $X, y$ and leakage audit reports.
* **Files / Modules Owned:** `src/prediction/features.py`, `src/prediction/train.py`, `tests/unit/test_leakage_guard.py`.
* **Deliverables:** Feature extraction module, temporal split pipeline, automated leakage guard test suite.
* **Tests & Validation:** `pytest tests/unit/test_leakage_guard.py` asserting zero future timestamp observations in feature matrices.
* **Acceptance Criteria:**
  - 100% reproducibility of feature matrices from identical scenario seeds.
  - Zero data leakage confirmed by automated tests.
* **Definition of Done:** Feature pipeline verified and leakage tests passing.
* **Explicit Non-Goals:** Complex neural network architectures.
* **Workstream Ownership:** Lakshay Bharti.
* **Execution Mode:** Independent workstream task on `features/lakshay-optimization-ml`.

---

## Phase 9: Predictive-Model Benchmarking & Selection

* **Phase Identifier:** `PHASE-9`
* **Objective:** Train, evaluate, and calibrate predictive models (LightGBM vs linear baselines) for maintenance failure risk and turnaround delay regression, exporting pure-Python inference artifacts.
* **Scope:** Logistic/Ridge baselines, LightGBM models, Platt/Isotonic calibration, Brier score evaluation, and lightweight inference service.
* **Prerequisites:** `PHASE-8` completed.
* **Input & Output Contracts:** In: Feature matrices $X, y$. Out: Calibrated model artifacts and `PredictiveAnalyticsService`.
* **Files / Modules Owned:** `src/prediction/models.py`, `src/prediction/service.py`, `configs/models/`, `models/checkpoints/`, `tests/unit/test_prediction_service.py`.
* **Deliverables:** Trained and calibrated model files, inference service, model evaluation report.
* **Tests & Validation:**
  - Classifier achieves $\text{ROC-AUC} \ge 0.75$, Brier score $\le 0.15$.
  - Regressor achieves $\text{MAE} \le 12$ minutes on test set.
  - Inference latency $< 20$ms on CPU for 100 assets.
* **Acceptance Criteria:**
  - LightGBM outperforms linear baseline by $\ge 15\%$ on validation set.
  - Pure-Python inference loads without heavy training dependencies.
* **Definition of Done:** Models validated, exported, and passing inference unit tests.
* **Explicit Non-Goals:** Real-time deep learning online training.
* **Workstream Ownership:** Lakshay Bharti.
* **Execution Mode:** Independent workstream task on `features/lakshay-optimization-ml`.

---

## Phase 10: Prediction-Aware Rolling-Horizon Optimisation

* **Phase Identifier:** `PHASE-10`
* **Objective:** Integrate calibrated predictive risks and turnaround buffers into the optimization engine, proving downstream operational benefits over reactive scheduling.
* **Scope:** Risk-aware CP-SAT solver, dynamic buffer injection, risk penalty weighting, and comparative downstream evaluation experiment.
* **Prerequisites:** `PHASE-7` and `PHASE-9` completed.
* **Input & Output Contracts:** In: State, predictions, solver config. Out: Disruption-resilient operational schedule and evaluation report.
* **Files / Modules Owned:** `src/optimization/risk_aware_solver.py`, `experiments/reports/prediction_value.md`.
* **Deliverables:** `RiskAwareOptimizationSolver`, downstream evaluation experiment report.
* **Tests & Validation:**
  - Execute 50-scenario benchmark comparing Reactive (No ML) vs Prediction-Aware scheduling.
  - Measure abort rate reduction and cascaded delay mitigation.
* **Acceptance Criteria:**
  - Statistically significant reduction in mission aborts ($\ge 30\%$) and cascaded delays ($\ge 20\%$) with $< 5\%$ degradation in task completion.
* **Definition of Done:** Downstream value proven and documented in evaluation report.
* **Explicit Non-Goals:** Unconstrained heuristic overrides of hard constraints.
* **Workstream Ownership:** Lakshay Bharti (Experimental evaluation by Nidhi Jha).
* **Execution Mode:** Collaborative integration between Lakshay and Nidhi.

---

## Phase 11: What-If Simulation, Robustness, & Integrated Evaluation

* **Phase Identifier:** `PHASE-11`
* **Objective:** Implement isolated counterfactual sandbox cloning, disruption injection operators, dynamic re-optimization, and the Plan Diff Analyzer, executing stress and robustness sweeps.
* **Scope:** `ScenarioSandbox`, disruption mutators (`GroundAircraft`, `CloseRunway`, `WeatherAlert`), `PlanDiffAnalyzer`, and headless benchmark sweeps.
* **Prerequisites:** `PHASE-5`, `PHASE-7`, and `PHASE-10` completed.
* **Input & Output Contracts:** In: Active state and disruption specifications. Out: Sandboxed revised plan and structured `PlanDelta`.
* **Files / Modules Owned:** `src/simulation/sandbox.py`, `src/simulation/disruptions.py`, `src/simulation/what_if_engine.py`, `src/simulation/diff_analyzer.py`, `experiments/benchmark_runner.py`, `tests/unit/test_what_if_engine.py`.
* **Deliverables:** What-If simulation engine, diff analyzer, robustness sweep scripts, publication-grade evaluation report.
* **Tests & Validation:**
  - Sandbox isolation test: modifying cloned state causes 0 byte mutations to baseline plan.
  - Replay test: identical disruption sequence yields identical diff metrics across 5 repeat evaluations.
* **Acceptance Criteria:**
  - Re-optimization executes in $< 10$s for 50-task disrupted scenarios.
  - Diff analyzer outputs structured JSON highlighting reassignments and delay shifts.
* **Definition of Done:** What-if engine verified and robustness evaluation report completed.
* **Explicit Non-Goals:** Monte Carlo tree search or reinforcement learning simulation.
* **Workstream Ownership:** Nidhi Jha.
* **Execution Mode:** Independent workstream task on `features/nidhi-validation-simulation`.

---

## Phase 12: Core API Contracts, Reproducible Release, & Frontend Handoff

* **Phase Identifier:** `PHASE-12`
* **Objective:** Expose all core operations via a production-grade FastAPI REST service, validate end-to-end integration, package reproducible configurations, and deliver stable contracts for the frontend team.
* **Scope:** REST routers (`scenarios`, `state`, `optimize`, `simulation`), end-to-end integration tests, OpenAPI 3.1 specification export, and frontend integration handoff documentation.
* **Prerequisites:** All prior phases (Phases 1 to 11) completed.
* **Input & Output Contracts:** In: HTTP requests from frontend / scripts. Out: Typed JSON responses adhering to OpenAPI spec.
* **Files / Modules Owned:** `src/api/main.py`, `src/api/routes/*.py`, `tests/integration/test_api_endpoints.py`, `docs/FRONTEND_HANDOFF.md`.
* **Deliverables:** Verified FastAPI backend, end-to-end integration test suite, OpenAPI schema export, frontend handoff guide.
* **Tests & Validation:**
  - `pytest tests/integration/test_api_endpoints.py` with 100% endpoint coverage.
  - Overall repository test coverage $\ge 85\%$.
* **Acceptance Criteria:**
  - Endpoints respond with valid HTTP status codes and strict Pydantic schemas.
  - Clean local launch verified with zero configuration overhead.
* **Definition of Done:** Full test suite passing, OpenAPI contracts frozen and exported, tag `v1.0.0` registered.
* **Explicit Non-Goals:** Developing the React frontend UI.
* **Workstream Ownership:** All three leads (Nakshatra: Routes, Nidhi: Tests, Lakshay: Contracts).
* **Execution Mode:** Final collaborative integration and handoff to the frontend team.
