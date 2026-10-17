# Workstream Specification: Nakshatra Yadav
## Data Foundation, Domain Modeling, Synthetic Generation & State Pipeline

**Role:** Senior Data Architect & Data Engineering Lead  
**Primary Workstream:** Data Foundation, Synthetic Generators & Canonical State Pipeline  
**Associated SIH Problem Statement:** SIH 26250 (Air Power: Dynamic Air Operations & Resource Optimisation)  
**Dedicated Branch:** `features/nakshatra-data-state`  

---

## 1. Primary Responsibilities & Scope Boundaries

Nakshatra Yadav owns the data foundation of AIRWISE, including external dataset evaluation, canonical domain entity schemas, procedural synthetic scenario generation, in-memory state management, data fusion, and event replay.

### Core Responsibilities:
1. **External Dataset Auditing & Provenance:** Execute evidence-backed investigation of open datasets (TU Delft, NASA C-MAPSS, US BTS, ROADEF); establish data provenance and licensing records.
2. **Data Security & Ingestion Threat Modeling:** Author the data security threat model and implement safe ingestion guards (decompression bomb limits, Zip-Slip prevention, type sanitization).
3. **Canonical Domain Schemas:** Define strongly-typed Pydantic v2 domain models (`Airbase`, `Runway`, `AirframeType`, `Aircraft`, `CrewMember`, `MaintenanceBay`, `OperationalTask`, `WeatherWindow`).
4. **Procedural Synthetic Scenario Generator:** Implement a deterministic, seed-controlled generator synthesizing multi-base operational scenarios with 100% referential integrity.
5. **Configurable Scenario Profiles:** Implement scenario scales from Small (10 sorties) and Medium (50 sorties) to Large (200 sorties) and Stress (500 sorties) with injected strain rates.
6. **Canonical Operational State:** Implement a thread-safe, in-memory state container providing $O(1)$ entity lookup by identifier and immutable snapshotting.
7. **Event Management & Replay Engine:** Model structured operational events (`AircraftGrounded`, `RunwayClosed`, `WeatherAlert`) and build a deterministic event replay and fusion engine.
8. **Shared Data Fixtures & Benchmark Sets:** Provide standardized JSON fixtures for solver and simulation benchmarking by Lakshay and Nidhi.
9. **Core REST Routing:** Scaffold primary FastAPI routes for scenario management, state inspection, and event ingestion (`src/api/routes/scenarios.py`, `state.py`).
10. **Test Authoring:** Author unit tests for domain validation, generator reproducibility, state replay equivalence, and safe ingestion guards.

### Explicit Scope Boundaries & Non-Goals:
- **Do NOT implement optimization algorithms:** Lakshay owns the CP-SAT and MILP solvers (`src/optimization/`), and Nidhi owns the Greedy baseline (`src/baselines/`).
- **Do NOT train machine learning models:** Lakshay owns feature extraction and model training (`src/prediction/`).
- **Do NOT build the independent feasibility auditor:** Nidhi owns independent constraint checking (`src/evaluation/`).
- **Do NOT implement frontend components:** Frontend is handled by external teammates.

---

## 2. Directory & Module Ownership

Nakshatra has sole primary ownership of the following directories and files:

```
src/
├── domain/
│   ├── __init__.py
│   ├── enums.py                  # CapabilityClass, MaintenanceStatus, TaskPriority
│   ├── models.py                 # Core Pydantic domain models
│   └── schemas.py                # Validation logic and serialization schemas
├── data/
│   ├── __init__.py
│   ├── adapters.py               # External dataset parsers (C-MAPSS, BTS samples)
│   └── safe_loader.py            # Decompression bomb and Zip-Slip guards
├── generator/
│   ├── __init__.py
│   ├── scenario_generator.py     # Procedural seed-controlled synthetic generator
│   └── profiles.py               # Standard scenario configurations (Nominal, Strained)
├── state/
│   ├── __init__.py
│   ├── canonical_state.py        # In-memory operational state container
│   ├── events.py                 # Structured operational event catalog
│   └── fusion_engine.py          # Event ingestion, ordering, and conflict resolution
├── api/
│   ├── routes/
│   │   ├── scenarios.py          # Scenario CRUD & generation endpoints
│   │   └── state.py              # Operational state inspection endpoints
configs/
└── data/
    └── scenario_profiles.yaml    # Parameter distributions for procedural generator
data/
└── scenarios/
    ├── demo_baseline.json        # Curated demonstration baseline scenario
    └── test_fixtures/            # Small debugging fixtures (5 to 50 tasks)
tests/unit/
├── test_domain_models.py         # Schema constraint and validation tests
├── test_generator_reproducibility.py  # Seed determinism and referential integrity
├── test_state_replay.py          # Event replay and hash equivalence tests
└── test_safe_ingestion.py        # Security threat mitigations
```

---

## 3. Public Interface Contracts

### 3.1 Provided Contracts (Exposed to Lakshay & Nidhi)
```python
# src/state/canonical_state.py
class CanonicalOperationalState:
    def __init__(self, scenario_id: str, epoch_timestamp: datetime):
        self.scenario_id: str = scenario_id
        self.epoch: datetime = epoch_timestamp
        self.airbases: dict[str, Airbase] = {}
        self.aircraft: dict[str, Aircraft] = {}
        self.crew: dict[str, CrewMember] = {}
        self.tasks: dict[str, OperationalTask] = {}
        self.weather: dict[str, list[WeatherWindow]] = {}
        self.current_minute: int = 0

    def snapshot(self) -> "CanonicalOperationalState":
        """Return an immutable deep-copy snapshot of current state."""
        return copy.deepcopy(self)

    def apply_event(self, event: OperationalEvent) -> None:
        """Apply an operational event and mutate state deterministically."""
        ...
```

```python
# src/generator/scenario_generator.py
@dataclass
class GeneratorConfig:
    seed: int = 42
    duration_hours: int = 24
    num_airbases: int = 3
    num_aircraft: int = 15
    num_crew: int = 30
    num_tasks: int = 50
    disruption_rate: float = 0.10

class SyntheticScenarioGenerator:
    def generate(self, config: GeneratorConfig) -> CanonicalOperationalState:
        """Generate a fully consistent, validated operational state."""
        ...
```

---

## 4. Detailed Task Breakdown & Implementation Sequence

| Phase | Task ID | Description | Prerequisites | Deliverables | Est. Days |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Phase 1** | `T1-01` | External dataset investigation, licensing, download verification | None | `docs/data-audit.md` | 2.0 |
| **Phase 1** | `T1-02` | Threat model, safe ingestion checklist, quarantine rules | `T1-01` | Security section of `docs/data-audit.md` | 1.0 |
| **Phase 3** | `T3-01` | Implement Pydantic v2 domain models (`Airbase`, `Aircraft`, `Crew`) | Lakshay `T2-01` | `src/domain/models.py`, `schemas.py` | 2.0 |
| **Phase 3** | `T3-02` | Author unit tests for schema validation and domain invariants | `T3-01` | `tests/unit/test_domain_models.py` | 1.0 |
| **Phase 4** | `T4-01` | Build procedural scenario generator with seed-based reproducibility | `T3-01` | `src/generator/scenario_generator.py` | 3.0 |
| **Phase 4** | `T4-02` | Implement scenario configuration profiles (Nominal, Strained, Extreme) | `T4-01` | `src/generator/profiles.py` | 1.5 |
| **Phase 4** | `T4-03` | Generate small debugging fixtures and large benchmark scenarios | `T4-02` | `data/scenarios/*.json` | 1.0 |
| **Phase 4** | `T4-04` | Author generator determinism and referential integrity tests | `T4-01` | `tests/unit/test_generator_reproducibility.py` | 1.0 |
| **Phase 5** | `T5-01` | Model structured operational events and immutable event envelopes | `T3-01` | `src/state/events.py` | 1.5 |
| **Phase 5** | `T5-02` | Implement in-memory `CanonicalOperationalState` container | `T5-01` | `src/state/canonical_state.py` | 2.0 |
| **Phase 5** | `T5-03` | Build Data Fusion Engine with timestamp sorting & conflict resolution | `T5-02` | `src/state/fusion_engine.py` | 2.5 |
| **Phase 5** | `T5-04` | Author state replay and snapshot immutability unit tests | `T5-03` | `tests/unit/test_state_replay.py` | 1.0 |
| **Phase 12** | `T12-01`| Implement FastAPI routes for scenarios, state inspection, and events | All services | `src/api/routes/scenarios.py`, `state.py` | 2.5 |

**Total Estimated Workload:** 21.0 Engineering Days (52 Story Points).

---

## 5. Testing & Quality Acceptance Criteria

1. **Deterministic Reproducibility:** Generator with identical random seed must output byte-identical JSON across repeated invocations.
2. **Referential Integrity:** 100% of generated task requirements, airbases, and runways must resolve to existing valid entity IDs (zero dangling references).
3. **Replay Equivalence:** Ingesting 200 operational events out-of-order must produce an identical state hash as chronological replay.
4. **Safe Ingestion Protection:** Ingestion loader must reliably reject archives exceeding 50 MB and archives containing path-traversal relative links (`../../`).
5. **Lookup Latency:** In-memory entity retrieval by identifier in `CanonicalOperationalState` must complete in $< 1.0$ms for fleets up to 1,000 units.

---

## 6. Deferred Planning Workflow (Mandatory Instruction)

> [!IMPORTANT]
> When Nakshatra's coding agent begins implementation:
> 1. Read `ARCHITECTURE.md`, `PHASES.md`, `ROADMAP.md`, `REQUIREMENTS.md`, and this document (`Nakshatra.md`).
> 2. Create `PHASES_NAKSHATRA.md` detailing granular implementation sub-phases.
> 3. Create `CHECKLIST_NAKSHATRA.md` tracking daily task completion with commit hashes.
> 4. Do not modify files outside `src/domain/`, `src/data/`, `src/generator/`, `src/state/`, and owned test directories.
