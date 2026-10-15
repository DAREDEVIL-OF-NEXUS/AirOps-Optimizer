# AIRWISE Architectural Decision Log (ADR)

This log records the foundational architectural decisions made for AIRWISE. Decisions are immutable once accepted; subsequent amendments must be recorded as superseding ADRs.

---

## ADR-001: Modular Monolith vs. Distributed Microservices Architecture

* **Status:** `ACCEPTED (Final)`
* **Date / Milestone:** Phase 0 / Milestone 0
* **Context:** The system requires tight coordination between data synthesis, state management, predictive inference, constraint solving, and persistence. Deploying these components as distributed microservices (e.g. separate Docker containers communicating over HTTP or message queues) introduces network overhead, serialized payloads, distributed transaction failure modes, and complex local orchestration.
* **Options Considered:**
  1. *Distributed Microservices:* Independent services for Generator, Predictor, Optimizer, and API, coordinated via RabbitMQ/Kafka.
  2. *Modular Monolith:* A single cohesive Python codebase with strictly defined internal package boundaries (`domain`, `state`, `prediction`, `optimization`, `api`) communicating via in-process typed interfaces.
* **Decision:** Implement a **Modular Monolith**.
* **Rationale:** A modular monolith maximizes execution speed (in-memory state lookups and zero network latency for what-if branching), simplifies developer setup, and facilitates direct automated unit testing without mock infrastructure.
* **Consequences & Trade-offs:**
  - *Positive:* Fast development iteration, zero network latency, unified deployment, single codebase tooling.
  - *Negative:* Long-running solver operations must be managed carefully using thread pools or background task executors within FastAPI to prevent blocking the event loop.

---

## ADR-002: Constraint Satisfaction & Optimization Engine

* **Status:** `ACCEPTED (Final)`
* **Date / Milestone:** Phase 0 / Milestone 0
* **Context:** Resource allocation in air operations involves interval scheduling (take-off, cruise, landing, turnaround), discrete resource assignment (specific airframe and crew matching), and complex logical constraints (mandatory rest hours, qualification matching).
* **Options Considered:**
  1. *Google OR-Tools CP-SAT (Constraint Programming with SAT):* Highly specialized for interval scheduling, cumulative resource constraints, and non-linear logic.
  2. *Mixed-Integer Linear Programming (MILP via SciPy / PuLP / CBC / Gurobi):* Standard linear programming approach; requires linearizing disjunctive temporal constraints (big-M formulations), which can degrade solver performance.
  3. *Genetic Algorithms / Heuristics:* Fast for large problems, but cannot prove optimality or certify mathematical infeasibility.
* **Decision:** Adopt **Google OR-Tools CP-SAT** as the primary solver, accompanied by a **Custom Deterministic Greedy Allocator** as a baseline.
* **Rationale:** CP-SAT provides native interval variables (`NewIntervalVar`) and global scheduling constraints (`AddNoOverlap`), which excel at preventing scheduling conflicts without cumbersome big-M formulations. Google OR-Tools is open-source, robust, and actively maintained.
* **Consequences & Trade-offs:**
  - *Positive:* Global constraints yield faster solving and concise formulations; proven feasibility guarantees; built-in multi-threading.
  - *Negative:* Objective values must be expressed as integers; continuous penalties (e.g. fractional minutes or costs) must be scaled to integer representations.

---

## ADR-003: Tabular Predictive Analytics Stack

* **Status:** `ACCEPTED (Final)`
* **Date / Milestone:** Phase 0 / Milestone 0
* **Context:** The system needs to forecast airframe unscheduled maintenance risks and flight turnaround delays based on historical logs, ambient conditions, and fleet utilization metrics.
* **Options Considered:**
  1. *Deep Sequence Models (LSTM, Transformer):* High capacity, but require massive training corpuses, high compute, and exhibit black-box behavior and high inference latency.
  2. *Gradient Boosted Decision Trees (LightGBM / scikit-learn HistGradientBoosting) & Linear Baselines (Ridge / Logistic Regression):* Industry standard for tabular operational data; fast training, low latency, easily calibrated, and highly interpretable.
* **Decision:** Adopt **scikit-learn** and **LightGBM** with explicit probability calibration (Platt scaling / Isotonic regression).
* **Rationale:** Operational tabular data does not justify deep learning bloat. Calibrated tree models offer superior accuracy, rapid inference ($< 20$ms), and clear feature importance metrics.
* **Consequences & Trade-offs:**
  - *Positive:* Tiny model artifact size, rapid CPU-only inference, zero GPU requirements.
  - *Negative:* Does not model raw natural language pilot logs without an intermediate NLP extraction step.

---

## ADR-004: In-Memory Canonical State with Relational Storage Backing

* **Status:** `ACCEPTED (Final)`
* **Date / Milestone:** Phase 0 / Milestone 0
* **Context:** The interactive "What-If" simulation engine requires instantaneous cloning of the operational state, applying mutations, and re-running the solver without corrupting or incurring I/O overhead on disk storage.
* **Options Considered:**
  1. *Direct Database Queries on Every Operation:* Persist every state change immediately to disk; query tables during optimization.
  2. *In-Memory Canonical State with Snapshotting & SQLite/PostgreSQL Backup:* Keep active operational state in memory using Python data structures; persist scenarios, event logs, and final plans to a relational database via SQLAlchemy.
* **Decision:** Adopt **In-Memory Canonical State with Relational Persistence**.
* **Rationale:** Memory cloning (`copy.deepcopy` or structured clone methods) runs in $< 5$ms, enabling near-instantaneous what-if sandbox branch creation. Relational persistence provides historical auditability.
* **Consequences & Trade-offs:**
  - *Positive:* High-speed what-if experimentation, clean separation between active runtime state and historical records.
  - *Negative:* Application restart drops active uncommitted in-memory sandboxes; persistent scenarios must be reloaded on startup.

---

## ADR-005: Strict Decoupling of Prediction and Mathematical Optimization

* **Status:** `ACCEPTED (Final)`
* **Date / Milestone:** Phase 0 / Milestone 0
* **Context:** A common failure mode in AI scheduling projects is using an LLM or predictive model to generate schedules directly, resulting in constraint hallucinations and physically impossible allocations.
* **Options Considered:**
  1. *End-to-end Machine Learning / Reinforcement Learning:* Train a neural policy to output schedules directly.
  2. *Strict Functional Separation:* Machine learning predicts *risks and delays*; the mathematical solver ingests these estimates as objective weights and buffers to compute *allocations*.
* **Decision:** Implement **Strict Functional Separation**.
* **Rationale:** Mathematical constraint solvers guarantee hard constraint satisfaction (no two aircraft on the same runway at the same minute, no flight hours exceeding safety limits). Machine learning handles uncertainty estimation; mathematical programming handles constraint satisfaction.
* **Consequences & Trade-offs:**
  - *Positive:* Zero hallucinations, mathematically guaranteed feasibility, transparent auditability.
  - *Negative:* Two distinct engineering disciplines (ML and Operations Research) must be integrated and maintained.

---

## ADR-006: Frontend Technology Architecture

* **Status:** `ACCEPTED (Final)`
* **Date / Milestone:** Phase 0 / Milestone 0
* **Context:** Operational planners require a dense, highly responsive dashboard displaying Gantt timelines, resource health, and side-by-side comparison views.
* **Options Considered:**
  1. *Server-Side Rendered (Jinja2 / Streamlit / Dash):* Faster to prototype initially, but struggles with complex interactive drag-and-drop Gantt charts and responsive multi-panel diffing.
  2. *Single Page Application (React 18 + TypeScript + Vite + Tailwind CSS):* High component reusability, rich ecosystem of timeline and charting libraries (Recharts), strict type safety.
* **Decision:** Adopt **React 18 + TypeScript + Vite + Tailwind CSS**.
* **Rationale:** High-density operational dashboards require fine-grained state management and fast DOM updates when toggling between what-if scenario branches.
* **Consequences & Trade-offs:**
  - *Positive:* Clean modern UI, rich component ecosystem, type safety across API client.
  - *Negative:* Requires Node.js toolchain and separate build step.

---

## ADR-007: Pure Synthetic Operational Data Policy

* **Status:** `ACCEPTED (Final)`
* **Date / Milestone:** Phase 0 / Milestone 0
* **Context:** The system must model air operations and fleet logistics without violating operational security, non-disclosure agreements, or defense classification protocols.
* **Options Considered:**
  1. *Sanitized Real Data:* Attempting to redact real operational flight schedules.
  2. *Pure Generative Synthetic Operational Data:* Formally generating all entities, coordinates, time windows, and resource parameters via procedural code.
* **Decision:** Adopt **Pure Generative Synthetic Operational Data**.
* **Rationale:** Eliminates all legal, classification, and security risks. Enables systematic parameter sweeping (e.g. generating scenarios with 10, 50, 100, 500 tasks) that real-world datasets rarely provide.
* **Consequences & Trade-offs:**
  - *Positive:* 100% public repository safe, freely shareable, perfectly reproducible, unrestricted experimentation.
  - *Negative:* Synthetic data distributions must be carefully tuned to avoid trivial or unrealistic operational dynamics.
