# AIRWISE Requirements Specification

## 1. Overview & Classification

This document specifies the prioritized Functional Requirements (`FR-xxx`) and Non-Functional Requirements (`NFR-xxx`) governing the AIRWISE system.

### Priority Levels
* **`P0 - Mandatory MVP`**: Essential for initial functional demonstrator verification.
* **`P1 - High Priority`**: Required for comprehensive scientific benchmarking and interactive usability.
* **`P2 - Medium Priority`**: Enhancements for advanced operational workflows and resilience.
* **`P3 - Low / Future`**: Post-MVP explorations and extensions.

---

## 2. Functional Requirements (FR)

### Data Synthesis & Domain Modeling

#### `FR-001` Procedural Scenario Synthesis
* **Priority:** `P0 - Mandatory MVP`
* **Description:** The system must generate self-consistent, deterministic synthetic operational scenarios parameterized by random seed, airbase count, aircraft count, and task volume.
* **Rationale:** Eliminates reliance on classified or proprietary military datasets while providing reproducible testbeds.
* **Acceptance Criteria:** Given seed $S$, identical output JSON is generated. Referential integrity between all assets, locations, and tasks is 100%.
* **Verification Method:** Automated unit tests asserting byte-identical output across repeated executions.
* **Dependencies:** None.

#### `FR-002` Canonical Operational State Representation
* **Priority:** `P0 - Mandatory MVP`
* **Description:** The system must maintain an in-memory, timestamped canonical state of all operational assets, runway statuses, and crew rosters.
* **Rationale:** Provides a unified source of truth for downstream predictive and optimization modules.
* **Acceptance Criteria:** State can be queried by entity ID in $O(1)$ time and serialized to JSON without circular references.
* **Verification Method:** Automated unit tests for entity insertion, lookup, and state snapshotting.
* **Dependencies:** `FR-001`.

#### `FR-003` Multi-Source Data Fusion & Ingestion
* **Priority:** `P1 - High Priority`
* **Description:** The system must ingest simulated asynchronous event feeds (weather warnings, maintenance logs) and resolve conflicts deterministically.
* **Rationale:** Simulates real-world operational environments where status updates arrive from disparate channels.
* **Acceptance Criteria:** Out-of-order events processed gracefully; highest-precedence source wins upon conflict.
* **Verification Method:** Integration test injecting out-of-order synthetic event streams.
* **Dependencies:** `FR-002`.

---

### Predictive Analytics

#### `FR-004` Unscheduled Maintenance Risk Prediction
* **Priority:** `P0 - Mandatory MVP`
* **Description:** The system must predict the probability $[0.0, 1.0]$ that an airframe will require unscheduled maintenance before completing its next scheduled sortie.
* **Rationale:** Proactively avoids scheduling aircraft at high risk of in-flight or pre-flight aborts.
* **Acceptance Criteria:** Model achieves ROC-AUC $\ge 0.75$ and Brier score $\le 0.18$ on out-of-sample synthetic evaluation data.
* **Verification Method:** Offline model validation script with strict temporal train/test split.
* **Dependencies:** `FR-002`.

#### `FR-005` Turnaround Delay Estimation
* **Priority:** `P1 - High Priority`
* **Description:** The system must estimate ground turnaround delay (in minutes) based on airbase congestion, weather conditions, and aircraft type.
* **Rationale:** Allows solver to insert dynamic turnaround buffers rather than static estimates.
* **Acceptance Criteria:** Regression MAE $\le 12$ minutes against ground-truth synthetic simulation.
* **Verification Method:** Cross-validation testing on synthetic historical logs.
* **Dependencies:** `FR-002`.

---

### Mathematical Optimisation

#### `FR-006` Constraint Satisfaction Optimization (CP-SAT)
* **Priority:** `P0 - Mandatory MVP`
* **Description:** The system must solve the task assignment and scheduling problem using Google OR-Tools CP-SAT, enforcing all hard constraints.
* **Rationale:** Ensures computed schedules are legally and physically feasible.
* **Acceptance Criteria:** Zero overlapping task assignments on any airframe; zero crew rest violations; solver respects configurable search timeout.
* **Verification Method:** Automated feasibility audit test suite asserting 0 hard constraint violations.
* **Dependencies:** `FR-002`, `FR-004`.

#### `FR-007` Heuristic Baseline Allocator
* **Priority:** `P0 - Mandatory MVP`
* **Description:** The system must implement a transparent, deterministic greedy heuristic allocator operating on the identical problem interface.
* **Rationale:** Provides an honest, non-vacuous benchmark against which the CP-SAT solver's performance is evaluated.
* **Acceptance Criteria:** Produces a feasible (or partially unassigned) schedule in $< 500$ms for 100 tasks.
* **Verification Method:** Unit test comparing greedy output against CP-SAT output.
* **Dependencies:** `FR-006`.

#### `FR-008` Explanation & Infeasibility Diagnosis
* **Priority:** `P1 - High Priority`
* **Description:** The system must explain why specific tasks were delayed or left unfulfilled, identifying binding constraints (e.g. lack of qualified crew, runway capacity exhausted).
* **Rationale:** Operators require transparent rationales to trust automated decision-support recommendations.
* **Acceptance Criteria:** Every unassigned task in an output plan is accompanied by a structured explanation code and resource bottleneck diagnosis.
* **Verification Method:** Automated assertion on over-constrained scenario instances.
* **Dependencies:** `FR-006`.

---

### Simulation & What-If Engine

#### `FR-009` Isolated Counterfactual Branching
* **Priority:** `P0 - Mandatory MVP`
* **Description:** The system must allow users to clone an existing operational plan into an isolated sandbox, inject disruptions, and re-optimize without mutating the baseline plan.
* **Rationale:** Core capability allowing planners to test contingencies risk-free.
* **Acceptance Criteria:** Cloned sandbox modification results in zero memory or database alterations to the original scenario.
* **Verification Method:** Unit test inspecting deep-equality of original scenario before and after sandbox execution.
* **Dependencies:** `FR-002`, `FR-006`.

#### `FR-010` Plan Differential Analyzer
* **Priority:** `P0 - Mandatory MVP`
* **Description:** The system must compute a structured diff between the original plan and the re-optimized plan, highlighting reassignments, delay shifts, and canceled tasks.
* **Rationale:** Planners need to instantly comprehend the ripple effect of a disruption.
* **Acceptance Criteria:** Output JSON explicitly details added, removed, and shifted flight legs with delta KPI metrics.
* **Verification Method:** Unit test verifying delta calculations against known synthetic mutations.
* **Dependencies:** `FR-009`.

---

### Delivery, API & User Interface

#### `FR-011` RESTful Application Programming Interface
* **Priority:** `P0 - Mandatory MVP`
* **Description:** The system must expose all core operations (scenario generation, state retrieval, optimization, simulation) via a typed FastAPI interface.
* **Rationale:** Decouples UI and automation scripts from core domain logic.
* **Acceptance Criteria:** All endpoints conform to OpenAPI 3.1 standards with valid Pydantic validation schemas.
* **Verification Method:** Automated `pytest` suite using FastAPI `TestClient`.
* **Dependencies:** `FR-001` through `FR-010`.

#### `FR-012` Interactive Operations Dashboard
* **Priority:** `P1 - High Priority`
* **Description:** The system must provide a web dashboard featuring Gantt schedules, resource health metrics, prediction badges, and what-if comparison views.
* **Rationale:** Human-in-the-loop operational decision support.
* **Acceptance Criteria:** Dashboard renders in modern web browsers (Chrome, Firefox, Edge) without client-side console errors.
* **Verification Method:** End-to-end browser component tests.
* **Dependencies:** `FR-011`.

---

## 3. Non-Functional Requirements (NFR)

### Performance & Scalability

#### `NFR-001` Optimization Runtime Bound
* **Priority:** `P0 - Mandatory MVP`
* **Description:** The solver must terminate and return the best-found feasible solution within a user-configurable time limit (default 30 seconds for scenarios up to 100 tasks).
* **Verification:** Benchmark execution with wall-clock timing assertions.

#### `NFR-002` State Query Latency
* **Priority:** `P0 - Mandatory MVP`
* **Description:** In-memory canonical state inspection and serialization must complete in $< 50$ms for up to 1,000 operational entities.
* **Verification:** Performance profiling in unit tests.

---

### Reliability & Integrity

#### `NFR-003` Determinism & Reproducibility
* **Priority:** `P0 - Mandatory MVP`
* **Description:** Given an identical random seed, scenario parameters, and solver configuration, the system must produce identical outputs across executions.
* **Verification:** CI test asserting checksum equality of scenario generations and optimization results across repeated runs.

#### `NFR-004` Persistence Portability
* **Priority:** `P1 - High Priority`
* **Description:** The persistence layer must function out-of-the-box using SQLite with zero external database configuration, while remaining 100% compatible with PostgreSQL.
* **Verification:** Test suite execution against both SQLite memory and PostgreSQL container.

---

### Maintainability, Code Quality & Governance

#### `NFR-005` Test Coverage Standards
* **Priority:** `P0 - Mandatory MVP`
* **Description:** Core backend domain, optimization, and state modules must maintain $\ge 85\%$ automated unit and integration test branch coverage.
* **Verification:** `pytest-cov` reporting in CI pipeline.

#### `NFR-006` Zero External Synthetic Contamination
* **Priority:** `P0 - Mandatory MVP`
* **Description:** No classified, operational, or proprietary military data or tactics may be committed or processed by the repository. All data schemas must be generic and synthetic.
* **Verification:** Static analysis scan and documentation audit.
