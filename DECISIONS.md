# AIRWISE Architectural Decision Log (ADR)

**Project:** AIRWISE — AI-Enabled Dynamic Air Operations & Resource Optimisation  
**SIH Problem Statement:** SIH 26250  
**Document Status:** Complete & Authoritative (ADR-001 through ADR-012)  
**Authors & Leads:** Lakshay Bharti, Nakshatra Yadav, Nidhi Jha  

---

## ADR-001: Modular Monolith vs. Distributed Microservices Architecture
* **Status:** `ACCEPTED (Final)`
* **Context:** The system requires rapid state cloning, sub-millisecond entity lookups, and fast re-optimization during what-if replanning. Microservices introduce serialization costs and network latency.
* **Decision:** Implement a **Modular Monolith** with strictly bounded internal packages.
* **Consequences:** Low deployment overhead, sub-millisecond state cloning, unified testing.

---

## ADR-002: Constraint Satisfaction & Optimization Engine
* **Status:** `ACCEPTED (Final)`
* **Context:** Resource allocation requires interval scheduling, cumulative movement limits, and disjunctive non-overlapping constraints.
* **Decision:** Adopt **Google OR-Tools CP-SAT** as the primary solver, accompanied by a **Deterministic Greedy Allocator** (Nidhi) as an honest comparative baseline.
* **Consequences:** Native interval variables (`AddNoOverlap`), proven optimality bounds, multi-threaded search.

---

## ADR-003: Tabular Predictive Analytics Stack
* **Status:** `ACCEPTED (Final)`
* **Context:** The system forecasts component failure risks and flight delays from tabular operational metrics.
* **Decision:** Adopt **scikit-learn** and **LightGBM** with Platt/Isotonic probability calibration.
* **Consequences:** Low latency (<20ms on CPU), small model artifacts, zero GPU requirements.

---

## ADR-004: In-Memory Canonical State with Relational Storage Backing
* **Status:** `ACCEPTED (Final)`
* **Context:** What-if simulation requires near-instantaneous cloning of operational state.
* **Decision:** Maintain active state in memory using Python data structures; persist scenarios, event streams, and benchmark logs to SQLite (local) or PostgreSQL (production) via SQLAlchemy 2.0.
* **Consequences:** Sub-5ms state cloning for sandbox branches; persistent audit trail.

---

## ADR-005: Strict Decoupling of Prediction and Mathematical Optimization
* **Status:** `ACCEPTED (Final)`
* **Context:** Direct scheduling via ML or LLMs leads to constraint hallucinations and physically impossible allocations.
* **Decision:** Implement **Strict Functional Separation**. ML estimates *risks and delays*; the mathematical solver ingests these estimates to compute *provably feasible allocations*.
* **Consequences:** Guaranteed hard constraint satisfaction; auditable trade-offs.

---

## ADR-006: Frontend Technology Architecture & Scope Boundary
* **Status:** `ACCEPTED (Final)`
* **Context:** Operators require a dense, reactive dashboard. The frontend is developed by a dedicated external team.
* **Decision:** Frontend is built with React 18, TypeScript, Vite, and Tailwind CSS. **Frontend implementation is outside the scope of the core three-person workstream.** Core team delivers typed API contracts and OpenAPI schemas.
* **Consequences:** Core team focuses exclusively on data, ML, optimization, and simulation.

---

## ADR-007: Pure Synthetic Operational Data Policy
* **Status:** `ACCEPTED (Final)`
* **Context:** Air operations data is frequently sensitive or classified.
* **Decision:** Adopt a **Pure Generative Synthetic Operational Data Policy**. No classified, confidential, or proprietary military data may be committed or processed.
* **Consequences:** 100% public repository safe, freely reproducible, unrestricted parameter sweeping.

---

## ADR-008: 13-Phase Milestone-Driven Architecture Lifecycle
* **Status:** `ACCEPTED (Final)`
* **Date / Milestone:** Phase 0 / Milestone 0
* **Context:** The project requires a disciplined progression from external dataset auditing through domain modeling, solver construction, predictive modeling, what-if replanning, and release handoff.
* **Decision:** Establish a formal **13-Phase Lifecycle** (Phases 0 through 12) mapping directly to Milestones M0 through M12.
* **Consequences:** Clear task prerequisites, explicit quality gates, auditable progress tracking.

---

## ADR-009: Three-Person Mutually Exclusive & Collectively Exhaustive Workstream Partitioning
* **Status:** `ACCEPTED (Final)`
* **Date / Milestone:** Phase 0 / Milestone 0
* **Context:** Three engineers (Lakshay Bharti, Nakshatra Yadav, Nidhi Jha) must implement the core system in parallel without modifying one another's source files or causing integration bottlenecks.
* **Decision:** Partition the core codebase into three mutually exclusive workstreams:
  - **Lakshay Bharti:** Optimization & ML Core (`src/optimization/`, `src/prediction/`).
  - **Nakshatra Yadav:** Data Foundation & State Pipeline (`src/domain/`, `src/data/`, `src/generator/`, `src/state/`).
  - **Nidhi Jha:** Validation, Baselines & Simulation (`src/baselines/`, `src/evaluation/`, `src/simulation/`, `experiments/`).
* **Consequences:** Zero default file ownership overlap, balanced workload (21–22 days per engineer), clear interface hand-offs.

---

## ADR-010: Hybrid External-Synthetic Dataset Strategy (Option B)
* **Status:** `ACCEPTED (Final)`
* **Date / Milestone:** Phase 0 / Milestone 1
* **Context:** Investigation of open datasets (TU Delft, NASA C-MAPSS, US BTS, ROADEF) revealed that no single public dataset contains joint aircraft-crew-task-runway operational data.
* **Decision:** Adopt **Option B (Hybrid Strategy)**:
  - Generate core integrated operational scenarios procedurally (`src/generator/`).
  - Utilize NASA C-MAPSS and US BTS subsets strictly as auxiliary offline benchmarks for ML models.
  - Utilize TU Delft and ROADEF instances strictly as optimization formulation references.
* **Consequences:** Eliminates external runtime data dependencies while anchoring models against peer-reviewed academic benchmarks.

---

## ADR-011: Constraint Programming Interval Scheduling Formulation
* **Status:** `ACCEPTED (Final)`
* **Date / Milestone:** Phase 0 / Milestone 2
* **Context:** Aircraft fleet scheduling involves non-overlapping disjunctive intervals and turnaround buffers. Formulating this in MILP requires large numbers of big-M binary variables, causing slow linear relaxations.
* **Decision:** Use **OR-Tools CP-SAT Interval Variables** (`NewIntervalVar`, `AddNoOverlap`) as the primary solver formulation, while retaining an optional MILP comparison in `src/optimization/milp_solver.py`.
* **Consequences:** Faster solving times, compact constraint representation, native interval propagation.

---

## ADR-012: Deferred Per-Person Phases and Checklists Workflow
* **Status:** `ACCEPTED (Final)`
* **Date / Milestone:** Phase 0 / Milestone 0
* **Context:** Creating individual checklist files prematurely risks architectural divergence before feature branch initialization.
* **Decision:** Defer the creation of individual phase and checklist files (`PHASES_<NAME>.md`, `CHECKLIST_<NAME>.md`) until each engineer begins feature implementation. No root `checklist.md` is created.
* **Consequences:** Ensures individual plans are derived directly from the final approved shared blueprints.
