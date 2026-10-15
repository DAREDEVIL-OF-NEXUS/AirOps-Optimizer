# AIRWISE Detailed Implementation Phases

This document provides the operational specification for every engineering phase of the AIRWISE system. Each phase is self-contained, sequentially dependent, and defined with rigorous acceptance criteria and explicit non-goals.

---

## Phase 0: Repository & Project Foundations

* **Identifier:** `PHASE-0`
* **Purpose:** Establish the repository baseline, configure Git remotes, define the modular architecture, draft governance documents, and establish the living task tracking matrix.
* **Prerequisites:** Empty repository folder and target GitHub remote.
* **Exact Tasks:**
  1. Inspect local and remote Git states to ensure safety.
  2. Initialize local Git repository with default branch `main`.
  3. Associate origin remote with `https://github.com/DAREDEVIL-OF-NEXUS/AirOps-Optimizer`.
  4. Create comprehensive `.gitignore` and `.env.example`.
  5. Author core project documentation: `README.md`, `ROADMAP.md`, `PHASES.md`, `COMPLETION.md`, `ARCHITECTURE.md`, `REQUIREMENTS.md`, `DECISIONS.md`, and `CONTRIBUTING.md`.
  6. Verify all documents for internal consistency and cross-link integrity.
* **Files or Modules Expected to Change:**
  - `.gitignore`
  - `.env.example`
  - `README.md`
  - `ROADMAP.md`
  - `PHASES.md`
  - `COMPLETION.md`
  - `ARCHITECTURE.md`
  - `REQUIREMENTS.md`
  - `DECISIONS.md`
  - `CONTRIBUTING.md`
* **Deliverables:** Complete project documentation suite, clean Git commit, clean working tree.
* **Tests & Validation:** Manual inspection of files, git status, git remote verification, markdown linting.
* **Acceptance Criteria:**
  - All 8 required `.md` files present and populated with substantive, domain-specific content.
  - No broken markdown references or placeholder sections.
  - Remote configured and synchronized.
* **Completion Conditions:** Documentation signed off and initial commit registered.
* **Explicitly Excluded Work:** Implementation of application code, installation of heavy ML or solver packages.

---

## Phase 1: Domain Model & Synthetic Scenario Generation

* **Identifier:** `PHASE-1`
* **Purpose:** Define strongly-typed domain entities and implement a deterministic, time-aware synthetic scenario generator capable of simulating realistic operational environments.
* **Prerequisites:** `PHASE-0` verified complete.
* **Exact Tasks:**
  1. Define Pydantic v2 core schemas: `Airbase`, `Runway`, `AirframeType`, `Aircraft`, `CrewQualification`, `CrewMember`, `MaintenanceBay`, `FuelDepot`, `OperationalTask`, `WeatherWindow`.
  2. Implement mathematical validation logic (e.g. task start < task end, valid location references, non-negative capacities).
  3. Implement `ScenarioConfig` parameter object (seed, duration_hours, asset_counts, disruption_rate).
  4. Implement `SyntheticScenarioGenerator` supporting deterministic procedural generation based on pseudo-random seeds.
  5. Include reference scenario profiles: "Nominal Operations", "Severe Resource Strain", "High Turnaround Demand".
  6. Build unit tests validating schema constraints and scenario generation reproducibility.
* **Files or Modules Expected to Change:**
  - `src/domain/__init__.py`
  - `src/domain/enums.py`
  - `src/domain/models.py`
  - `src/domain/schemas.py`
  - `src/generator/__init__.py`
  - `src/generator/scenario_generator.py`
  - `src/generator/profiles.py`
  - `tests/unit/test_domain_models.py`
  - `tests/unit/test_scenario_generator.py`
  - `requirements.txt`
* **Deliverables:** Validated domain models, procedural scenario generator, unit test suite with 100% pass rate.
* **Tests & Validation:**
  - `pytest tests/unit/test_domain_models.py`
  - `pytest tests/unit/test_scenario_generator.py`
  - Verify deterministic identity: generator with seed=42 outputs byte-for-byte identical scenario JSON across repeated runs.
* **Acceptance Criteria:**
  - Zero schema validation warnings on generated scenarios.
  - 100% referential integrity (no unassigned or non-existent airbase/aircraft IDs).
  - Configurable generation scales from 10 to 500 tasks in < 2.0 seconds.
* **Completion Conditions:** All unit tests pass and code linting cleanly passes Ruff without warnings.
* **Explicitly Excluded Work:** Real database persistence, UI, API routing.

---

## Phase 2: State Management & Data Fusion

* **Identifier:** `PHASE-2`
* **Purpose:** Create an in-memory, thread-safe canonical operational state manager that consumes synthetic scenario data and real-time operational events, resolving conflicts deterministically.
* **Prerequisites:** `PHASE-1` verified complete.
* **Exact Tasks:**
  1. Define structured event envelope: `OperationalEvent` (event_id, timestamp, event_type, source, payload).
  2. Implement event catalog: `AircraftGroundedEvent`, `RunwayMaintenanceEvent`, `WeatherAlertEvent`, `SortieDelayedEvent`.
  3. Create `CanonicalOperationalState` container holding indexed lookup structures for assets, crews, and tasks.
  4. Implement `DataFusionEngine` handling ingestion, timestamp ordering, and conflict resolution (e.g. sensor telemetry vs. manual log precedence).
  5. Implement state snapshotting and rollback mechanism.
  6. Add unit and integration tests for out-of-order event streams and edge cases.
* **Files or Modules Expected to Change:**
  - `src/state/__init__.py`
  - `src/state/events.py`
  - `src/state/canonical_state.py`
  - `src/state/fusion_engine.py`
  - `tests/unit/test_state_management.py`
  - `tests/unit/test_data_fusion.py`
* **Deliverables:** State container, event ingestion engine, state snapshot serialization, comprehensive test suite.
* **Tests & Validation:**
  - `pytest tests/unit/test_state_management.py`
  - `pytest tests/unit/test_data_fusion.py`
  - Assert out-of-order event replay reaches identical end state as chronological replay.
* **Acceptance Criteria:**
  - Canonical state update completes in < 5ms for batch of 100 events.
  - State immutability guarantees: snapshots cannot be mutated by downstream consumers.
* **Completion Conditions:** All fusion and state transition tests pass cleanly.
* **Explicitly Excluded Work:** External message broker (Kafka/RabbitMQ), persistent SQL storage.

---

## Phase 3: Feasibility Model & Optimisation Baseline

* **Identifier:** `PHASE-3`
* **Purpose:** Formalize operational scheduling constraints and soft objectives; build the primary CP-SAT constraint programming solver and a transparent greedy benchmark algorithm.
* **Prerequisites:** `PHASE-2` verified complete.
* **Exact Tasks:**
  1. Define abstract `SolverInterface` (`solve(state, config) -> OptimizationResult`).
  2. Implement hard constraint formulations:
     - Resource availability windows.
     - Single-task allocation per aircraft/crew at any given time (no overlapping intervals).
     - Crew qualification and minimum rest-period rules.
     - Runway take-off and landing slot limits.
     - Aircraft type payload and capability requirements.
  3. Implement soft multi-objective penalty/reward functions:
     - Reward for completing high-priority operational tasks.
     - Linear penalty for task schedule delays.
     - Penalty for excess crew duty hours.
     - Regularization penalty to minimize schedule perturbation.
  4. Implement `CPSatOptimizationSolver` using Google OR-Tools CP-SAT.
  5. Implement `GreedyBaselineSolver` using deterministic heuristic rule ordering.
  6. Create `FeasibilityValidator` to independently audit allocations against hard constraints.
  7. Implement infeasibility diagnosis reporting (detecting which constraints are binding).
* **Files or Modules Expected to Change:**
  - `src/optimization/__init__.py`
  - `src/optimization/solver_interface.py`
  - `src/optimization/constraints.py`
  - `src/optimization/objectives.py`
  - `src/optimization/cp_sat_solver.py`
  - `src/optimization/greedy_solver.py`
  - `src/optimization/validator.py`
  - `tests/unit/test_optimization_solvers.py`
  - `tests/unit/test_feasibility_validator.py`
* **Deliverables:** Dual solver implementations (CP-SAT and Greedy), independent feasibility audit module, comprehensive optimization test suite.
* **Tests & Validation:**
  - `pytest tests/unit/test_optimization_solvers.py`
  - Verify that `FeasibilityValidator.audit(allocation)` returns zero violations for all feasible runs.
  - Verify CP-SAT solver objective value >= Greedy baseline solver across 10 distinct test scenarios.
* **Acceptance Criteria:**
  - Infeasible scenarios reliably identified without crashing or infinite loops.
  - Solver time limit enforced strictly (e.g. terminates cleanly at 30 seconds with best-found solution).
* **Completion Conditions:** Both solvers pass comparative unit tests and feasibility audit.
* **Explicitly Excluded Work:** Dynamic heuristic learning, GPU solvers.

---

## Phase 4: Predictive Analytics Service

* **Identifier:** `PHASE-4`
* **Purpose:** Train, calibrate, and serve machine-learning models predicting operational disruption probabilities (unscheduled maintenance and turnaround delays).
* **Prerequisites:** `PHASE-2` verified complete.
* **Exact Tasks:**
  1. Define predictive target variables: `maintenance_failure_risk` (binary classification) and `turnaround_delay_minutes` (continuous regression).
  2. Implement feature engineering extraction from canonical state and asset utilization histories (e.g. cumulative flight hours, days since last overhaul, ambient temperature).
  3. Establish reproducible train/validation/test splits (temporal split to prevent data leakage).
  4. Train baseline models: Logistic Regression and Ridge.
  5. Train boosted tree models: LightGBM / HistGradientBoosting.
  6. Calibrate classification probabilities using Platt scaling or Isotonic Regression; compute Brier score and log loss.
  7. Package models into lightweight, serializable inference pipeline (`PredictiveAnalyticsService`).
  8. Connect predictions into scenario risk annotations for optimization buffer adjustments.
* **Files or Modules Expected to Change:**
  - `src/prediction/__init__.py`
  - `src/prediction/features.py`
  - `src/prediction/train.py`
  - `src/prediction/models.py`
  - `src/prediction/service.py`
  - `tests/unit/test_predictive_service.py`
* **Deliverables:** Feature engineering pipeline, trained and calibrated model artifacts, inference service, evaluation notebook/report.
* **Tests & Validation:**
  - `pytest tests/unit/test_predictive_service.py`
  - Verify model out-performs dummy/mean baseline by >= 15% on validation set.
  - Verify inference latency < 20ms per prediction batch.
* **Acceptance Criteria:**
  - Brier score for maintenance risk < 0.15.
  - Delay regression MAE within 12 minutes on synthetic test set.
  - Models load seamlessly in pure inference mode without re-training dependencies.
* **Completion Conditions:** Model evaluation metrics verified and unit tests passing.
* **Explicitly Excluded Work:** Deep neural networks, LLM integrations, computer vision.

---

## Phase 5: Scenario Simulation & Re-optimisation (What-If Engine)

* **Identifier:** `PHASE-5`
* **Purpose:** Implement counterfactual scenario branch creation, controlled disruption injection, re-optimization, and automated comparative plan diffing.
* **Prerequisites:** `PHASE-3` and `PHASE-4` verified complete.
* **Exact Tasks:**
  1. Build `ScenarioSandbox` allowing deep cloning of canonical states without mutating source plans.
  2. Implement disruption mutation operators:
     - `GroundAircraftDisruption(aircraft_id, reason)`
     - `CloseRunwayDisruption(runway_id, start_time, end_time)`
     - `WeatherDegradationDisruption(airbase_id, weather_severity)`
     - `TaskDelayDisruption(task_id, delay_minutes)`
  3. Implement re-optimization pipeline: mutate state -> update predictive risks -> re-run CP-SAT solver with warm start or schedule perturbation penalty.
  4. Implement `PlanDiffAnalyzer` calculating exact schedule delta metrics:
     - Reassigned tasks count.
     - Net delay variance.
     - Cancelled/unassigned tasks delta.
     - Crew duty-hour shifts.
  5. Unit test deterministic what-if replayability.
* **Files or Modules Expected to Change:**
  - `src/simulation/__init__.py`
  - `src/simulation/sandbox.py`
  - `src/simulation/disruptions.py`
  - `src/simulation/diff_analyzer.py`
  - `tests/unit/test_what_if_engine.py`
* **Deliverables:** Sandbox cloning engine, disruption operators, diff analyzer, comprehensive test suite.
* **Tests & Validation:**
  - `pytest tests/unit/test_what_if_engine.py`
  - Assert that applying disruption D to Scenario S produces identical output diffs over 5 repeat evaluations.
  - Assert source scenario state remains 100% byte-unmodified after what-if execution.
* **Acceptance Criteria:**
  - Re-optimization executes cleanly under disruption conditions.
  - Diff analyzer outputs structured, UI-ready JSON detailing exact changes.
* **Completion Conditions:** All simulation and diffing tests pass.
* **Explicitly Excluded Work:** Monte Carlo stochastic branching beyond single counterfactual scenarios.

---

## Phase 6: REST API & Persistence Layer

* **Identifier:** `PHASE-6`
* **Purpose:** Expose operational capabilities via a robust FastAPI service backed by an asynchronous/relational persistence model.
* **Prerequisites:** `PHASE-1` through `PHASE-5` verified complete.
* **Exact Tasks:**
  1. Setup database layer with SQLAlchemy 2.0 (SQLite default, PostgreSQL compatible).
  2. Implement database models for persistent scenarios, event logs, solver runs, and plan diffs.
  3. Implement repository pattern for database transactions.
  4. Implement FastAPI application factory with CORS middleware, exception handlers, and structured logging.
  5. Create modular API route routers:
     - `/api/v1/scenarios` (CRUD, seed generator)
     - `/api/v1/state` (Current operational state inspection)
     - `/api/v1/predictions` (Run disruption risk predictions)
     - `/api/v1/optimize` (Trigger CP-SAT or Baseline solver)
     - `/api/v1/simulation` (Execute what-if counterfactuals)
  6. Write automated API integration tests with `httpx` and `pytest`.
* **Files or Modules Expected to Change:**
  - `src/db/__init__.py`
  - `src/db/session.py`
  - `src/db/models.py`
  - `src/db/repositories.py`
  - `src/api/__init__.py`
  - `src/api/main.py`
  - `src/api/deps.py`
  - `src/api/routes/scenarios.py`
  - `src/api/routes/state.py`
  - `src/api/routes/predictions.py`
  - `src/api/routes/optimize.py`
  - `src/api/routes/simulation.py`
  - `tests/integration/test_api_endpoints.py`
* **Deliverables:** Production-ready FastAPI backend, relational database schema, integration test suite.
* **Tests & Validation:**
  - `pytest tests/integration/test_api_endpoints.py`
  - Verify OpenAPI JSON schema generation at `/openapi.json`.
* **Acceptance Criteria:**
  - Endpoints respond with valid HTTP status codes and strict Pydantic schemas.
  - Error responses include machine-readable error codes and human-readable diagnostic messages.
* **Completion Conditions:** All API integration tests pass with 100% router coverage.
* **Explicitly Excluded Work:** Complex authentication/OAuth2 (kept local for decision-support prototype).

---

## Phase 7: Frontend Decision-Support Dashboard

* **Identifier:** `PHASE-7`
* **Purpose:** Build a modern, responsive, high-density React web application providing operators with visual schedules, resource utilization, prediction alerts, and what-if comparisons.
* **Prerequisites:** `PHASE-6` verified complete.
* **Exact Tasks:**
  1. Scaffold frontend using Vite with React 18, TypeScript, and Tailwind CSS.
  2. Create typed API client interacting with backend REST endpoints.
  3. Implement core UI layouts:
     - **Operational Overview:** KPI summary cards (Fleet Readiness, Duty Hours, Flight Delays).
     - **Gantt Schedule View:** Timeline of aircraft sorties, maintenance blocks, and crew assignments.
     - **Resource Fleet Table:** Real-time health, qualification status, and location breakdown.
     - **Predictive Risk Panel:** Probability badges for equipment degradation and weather risks.
     - **What-If Counterfactual Sandbox:** Disruption injection modal and before/after side-by-side plan comparator.
  4. Implement data visualization using Recharts (Utilization charts, Objective trade-off Pareto scatter, delay distribution).
  5. Add frontend unit and component tests using Vitest and React Testing Library.
* **Files or Modules Expected to Change:**
  - `frontend/package.json`
  - `frontend/vite.config.ts`
  - `frontend/src/App.tsx`
  - `frontend/src/api/client.ts`
  - `frontend/src/components/GanttView.tsx`
  - `frontend/src/components/ResourceTable.tsx`
  - `frontend/src/components/PredictionAlerts.tsx`
  - `frontend/src/components/WhatIfComparator.tsx`
  - `frontend/src/components/KPIOverview.tsx`
  - `frontend/tests/*`
* **Deliverables:** Fully functional React/TypeScript frontend application.
* **Tests & Validation:**
  - `npm run build` succeeds without TypeScript compiler errors.
  - `npm run test` passes all component tests.
* **Acceptance Criteria:**
  - Dashboard renders operational scenario within 1.0s.
  - Interactive disruption injection updates side-by-side comparison cleanly.
* **Completion Conditions:** Frontend builds cleanly and passes end-to-end integration tests with backend.
* **Explicitly Excluded Work:** Mobile responsive views (designed for desktop/ops-centre displays).

---

## Phase 8: Integrated Validation & Experimental Benchmarks

* **Identifier:** `PHASE-8`
* **Purpose:** Execute rigorous scientific evaluation measuring optimization quality, solver scalability, baseline comparative advantage, and predictive model calibration.
* **Prerequisites:** `PHASE-1` through `PHASE-7` verified complete.
* **Exact Tasks:**
  1. Create automated benchmarking harness `experiments/benchmark_runner.py`.
  2. Define experimental test matrix:
     - Scenario sizes: Small (10 tasks), Medium (50 tasks), Large (150 tasks), Stress (300 tasks).
     - Disruption rates: 0% (nominal), 10% (moderate), 30% (severe).
     - Solvers: CP-SAT (30s limit), CP-SAT (60s limit), Greedy Baseline.
  3. Record metrics: Feasibility rate, objective value, runtime seconds, task completion rate, average delay per task, solver memory footprint.
  4. Generate publication-grade plots and CSV export in `experiments/results/`.
  5. Document experimental conclusions and formal solver comparisons in `experiments/EVALUATION_REPORT.md`.
* **Files or Modules Expected to Change:**
  - `experiments/benchmark_runner.py`
  - `experiments/metrics.py`
  - `experiments/plots.py`
  - `experiments/EVALUATION_REPORT.md`
  - `experiments/results/*`
* **Deliverables:** Benchmark harness, empirical experiment dataset, evaluation analysis report.
* **Tests & Validation:**
  - Automated execution of benchmark harness on fixed test seeds.
  - Statistical significance t-test confirming CP-SAT objective superiority over Greedy.
* **Acceptance Criteria:**
  - All experimental data strictly reproducible from documented seeds.
  - Clear reporting of runtime limits and optimality gaps.
* **Completion Conditions:** Benchmark report written and verified with reproducible figures.
* **Explicitly Excluded Work:** Fabricated or cherry-picked performance metrics.

---

## Phase 9: Demonstration Readiness & Release Packaging

* **Identifier:** `PHASE-9`
* **Purpose:** Deliver a turnkey, zero-friction demonstration package with pre-seeded scenarios, automated launch scripts, and comprehensive operator guides.
* **Prerequisites:** `PHASE-8` verified complete.
* **Exact Tasks:**
  1. Create curated demo scenario bundle (`data/scenarios/demo_baseline.json`, `demo_disrupted.json`).
  2. Implement unified single-command runner script `run_demo.py` starting both backend and frontend.
  3. Write step-by-step user walkthrough guide with screenshots and scenario explanations.
  4. Perform clean-room installation validation from a fresh directory.
  5. Tag and register final MVP release.
* **Files or Modules Expected to Change:**
  - `run_demo.py`
  - `scripts/setup_dev.py`
  - `docs/DEMO_GUIDE.md`
  - `README.md`
* **Deliverables:** Turnkey demo launcher, pre-seeded datasets, step-by-step demonstration walkthrough.
* **Tests & Validation:**
  - Fresh clone into isolated temporary folder; execute `run_demo.py`; verify full stack readiness in < 3 minutes.
* **Acceptance Criteria:**
  - Zero manual manual database configuration required for demo run.
  - Smooth demonstration flow without terminal crashes or console errors.
* **Completion Conditions:** Demonstration verified on clean local machine.
* **Explicitly Excluded Work:** Commercial cloud deployment (AWS/GCP/Azure) — local decision support target.
