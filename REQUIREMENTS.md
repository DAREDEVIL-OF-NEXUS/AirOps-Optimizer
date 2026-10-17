# AIRWISE Requirements Specification

**Project:** AIRWISE — AI-Enabled Dynamic Air Operations & Resource Optimisation  
**SIH Problem Statement:** SIH 26250  
**Document Status:** Complete & Verified Baseline  
**Authors & Leads:** Lakshay Bharti, Nakshatra Yadav, Nidhi Jha  

---

## 1. Functional Requirements (FR)

### Data Engineering & Synthetic Generation (Nakshatra Yadav)

#### `FR-001` External Dataset Auditing & Safe Ingestion
* **Priority:** `P0 - Mandatory MVP`
* **Description:** The system must inspect external benchmark datasets (4TU, NASA, BTS) against documented SHA-256 hashes, enforcing strict file size caps (<50MB) and directory traversal guards.
* **Acceptance Criteria:** Any file exceeding 50 MB uncompressed or containing relative path traversal (`../`) is quarantined safely without crashing.
* **Verification Method:** Unit tests in `tests/unit/test_safe_ingestion.py`.

#### `FR-002` Strongly-Typed Canonical Domain Modeling
* **Priority:** `P0 - Mandatory MVP`
* **Description:** The system must model all operational entities (`Airbase`, `Runway`, `AirframeType`, `Aircraft`, `CrewMember`, `OperationalTask`, `WeatherWindow`) using Pydantic v2 schemas with explicit physical units.
* **Acceptance Criteria:** Negative capacities, inverted time windows ($LST < EST$), and invalid identifier formats are rejected with descriptive validation errors.
* **Verification Method:** Unit tests in `tests/unit/test_domain_models.py`.

#### `FR-003` Deterministic Procedural Scenario Generation
* **Priority:** `P0 - Mandatory MVP`
* **Description:** The system must synthesize operational scenarios across configurable scales (Small: 10 sorties to Large: 200 sorties) controlled by integer pseudo-random seeds.
* **Acceptance Criteria:** Identical seed produces byte-identical output JSON; 100% referential integrity across assets, crews, and locations (0 dangling keys).
* **Verification Method:** Unit tests in `tests/unit/test_generator_reproducibility.py`.

#### `FR-004` In-Memory Canonical Operational State & Snapshotting
* **Priority:** `P0 - Mandatory MVP`
* **Description:** The system must maintain an in-memory, thread-safe operational state container supporting $O(1)$ entity retrieval by ID and deep-copy snapshots.
* **Acceptance Criteria:** Entity lookups complete in $< 1.0$ms; state snapshots clone in $< 5.0$ms for 500 entities.
* **Verification Method:** Unit tests in `tests/unit/test_state_management.py`.

#### `FR-005` Data Fusion & Deterministic Event Replay
* **Priority:** `P0 - Mandatory MVP`
* **Description:** The system must ingest asynchronous operational events (`AircraftGrounded`, `RunwayClosed`), ordering them chronologically and resolving conflicts deterministically.
* **Acceptance Criteria:** Out-of-order event replay produces an identical final state hash as chronological replay.
* **Verification Method:** Unit tests in `tests/unit/test_state_replay.py`.

---

### Feasibility, Optimisation & Evaluation (Lakshay Bharti & Nidhi Jha)

#### `FR-006` Independent Feasibility Auditing
* **Priority:** `P0 - Mandatory MVP`
* **Owner:** Nidhi Jha
* **Description:** The system must independently audit candidate schedules against all hard physical/regulatory constraints without relying on solver variables.
* **Acceptance Criteria:** Injected overlapping sorties, unqualified crew, or duty-hour breaches are flagged with 100% precision and recall.
* **Verification Method:** Unit tests in `tests/unit/test_feasibility_auditor.py`.

#### `FR-007` Deterministic Greedy Baseline Allocator
* **Priority:** `P0 - Mandatory MVP`
* **Owner:** Nidhi Jha
* **Description:** The system must implement a transparent, deterministic Earliest-Deadline-First greedy allocator to serve as an honest comparative benchmark.
* **Acceptance Criteria:** Produces a valid (feasible or partial) allocation in $< 50$ms for 100 tasks on standard CPU.
* **Verification Method:** Unit tests in `tests/unit/test_baselines.py`.

#### `FR-008` Constraint Satisfaction Optimization (Google OR-Tools CP-SAT)
* **Priority:** `P0 - Mandatory MVP`
* **Owner:** Lakshay Bharti
* **Description:** The system must solve the multi-resource allocation and scheduling problem using Google OR-Tools CP-SAT, enforcing interval disjunctions and cumulative runway slots.
* **Acceptance Criteria:** Zero hard constraint violations verified by the independent auditor; CP-SAT objective $\ge$ Greedy baseline across 100% of benchmark scenarios.
* **Verification Method:** Benchmark comparison in `tests/unit/test_optimization_solver.py`.

#### `FR-009` Scaled Integer Objective & Timeout Handling
* **Priority:** `P0 - Mandatory MVP`
* **Owner:** Lakshay Bharti
* **Description:** The solver must scale continuous probabilities and penalties to integer CP-SAT coefficients ($K_{\text{scale}} = 10,000$) and enforce strict search timeouts (`time_limit_seconds ± 0.5s`).
* **Acceptance Criteria:** Terminating at timeout returns best primal solution with audited optimality gap without crashing or hanging.
* **Verification Method:** Unit tests in `tests/unit/test_solver_timeout.py`.

---

### Predictive Analytics & Integration (Lakshay Bharti & Nidhi Jha)

#### `FR-010` Feature Pipeline with Strict Temporal Guards
* **Priority:** `P0 - Mandatory MVP`
* **Owner:** Lakshay Bharti
* **Description:** The system must extract asset fatigue and environmental features strictly using events with $t \le t_{\text{cut}}$, preventing lookahead leakage.
* **Acceptance Criteria:** Unit test asserts zero future timestamp observations in training feature matrices.
* **Verification Method:** Unit tests in `tests/unit/test_leakage_guard.py`.

#### `FR-011` Calibrated Predictive Maintenance & Turnaround Delay Models
* **Priority:** `P0 - Mandatory MVP`
* **Owner:** Lakshay Bharti
* **Description:** The system must train and calibrate LightGBM models predicting unscheduled failure probability ($P(\text{failure})$) and turnaround delay minutes ($E[\text{delay}]$).
* **Acceptance Criteria:** Classifier achieves $\text{ROC-AUC} \ge 0.75$ and Brier score $\le 0.15$; inference latency $< 20$ms on CPU.
* **Verification Method:** Unit tests in `tests/unit/test_prediction_service.py`.

#### `FR-012` Prediction-Aware Rolling-Horizon Optimization
* **Priority:** `P0 - Mandatory MVP`
* **Owner:** Lakshay Bharti & Nidhi Jha
* **Description:** The system must inject calibrated failure risk penalties and dynamic turnaround buffers into the optimization solver, proving downstream operational benefits.
* **Acceptance Criteria:** Benchmarks show $\ge 30\%$ reduction in mission aborts and $\ge 20\%$ reduction in cascaded delays compared to reactive scheduling.
* **Verification Method:** Experimental evaluation report in `experiments/reports/prediction_value.md`.

---

### Simulation, API & Delivery (Nidhi Jha & Nakshatra Yadav)

#### `FR-013` Counterfactual What-If Sandbox & Plan Diff Analyzer
* **Priority:** `P0 - Mandatory MVP`
* **Owner:** Nidhi Jha
* **Description:** The system must clone operational states into an isolated sandbox, apply disruption operators (`GroundAircraft`, `CloseRunway`), re-optimize, and output structured schedule diffs.
* **Acceptance Criteria:** Sandbox mutation causes zero modifications to the baseline plan; diff analyzer details exact reassignments and delay shifts.
* **Verification Method:** Unit tests in `tests/unit/test_what_if_engine.py`.

#### `FR-014` Asynchronous REST Application Programming Interface
* **Priority:** `P0 - Mandatory MVP`
* **Owner:** Nakshatra Yadav
* **Description:** The system must expose all core capabilities (scenarios, state, optimization, simulation) via typed FastAPI endpoints adhering to OpenAPI 3.1.
* **Acceptance Criteria:** Endpoints return valid HTTP status codes and strict Pydantic schemas; sub-100ms response time for state and diff lookups.
* **Verification Method:** Integration tests in `tests/integration/test_api_endpoints.py`.

#### `FR-015` Frontend Integration Contract Handoff
* **Priority:** `P0 - Mandatory MVP`
* **Owner:** Lakshay Bharti
* **Description:** The system must deliver frozen, typed API contracts, TypeScript type definitions, and an OpenAPI schema export for the external frontend team.
* **Acceptance Criteria:** Complete `docs/FRONTEND_HANDOFF.md` and `openapi.json` verified against frontend data requirements.
* **Verification Method:** Automated contract validation in `tests/integration/test_frontend_contracts.py`.

---

## 2. Non-Functional Requirements (NFR)

* **`NFR-001` Optimization Runtime Bound:** The solver must terminate within user-configured limits (default 30 seconds for scenarios up to 100 tasks).
* **`NFR-002` State Query Latency:** In-memory canonical state inspection must complete in $< 50$ms for up to 1,000 operational entities.
* **`NFR-003` Determinism & Reproducibility:** Identical random seed, parameters, and solver configuration must produce byte-identical outputs across executions.
* **`NFR-004` Persistence Portability:** Persistence layer must function out-of-the-box using SQLite with zero setup, maintaining 100% compatibility with PostgreSQL.
* **`NFR-005` Test Coverage Standards:** Core backend domain, state, optimization, and simulation modules must maintain $\ge 85\%$ automated branch coverage.
* **`NFR-006` Zero Operational Contamination:** Under no circumstances may classified, confidential, or proprietary military data or tactics be committed or processed.
* **`NFR-007` Ingestion Threat Protection:** Decompression bomb guards (<50MB) and Zip-Slip path traversal mitigations must be enforced on all external archives.
* **`NFR-008` Pure-Python Inference Deployment:** Predictive inference must execute on CPU in pure Python without requiring GPU accelerators or training dependencies.
