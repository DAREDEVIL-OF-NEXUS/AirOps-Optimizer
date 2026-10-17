# Contributing to AIRWISE

**Project:** AIRWISE — AI-Enabled Dynamic Air Operations & Resource Optimisation  
**SIH Problem Statement:** SIH 26250  
**Authors & Leads:** Lakshay Bharti, Nakshatra Yadav, Nidhi Jha  

---

## 1. Governance & Three-Person Workstream Model

Core engineering development is partitioned into three mutually exclusive, collectively exhaustive workstreams. Before modifying any code, review your designated ownership specification:

1. **Lakshay Bharti (`Lakshay.md`):** Optimisation Core & Predictive ML (`src/optimization/`, `src/prediction/`). Branch: `features/lakshay-optimization-ml`.
2. **Nakshatra Yadav (`Nakshatra.md`):** Data Foundation, Schemas, Generator & State (`src/domain/`, `src/data/`, `src/generator/`, `src/state/`). Branch: `features/nakshatra-data-state`.
3. **Nidhi Jha (`Nidhi.md`):** Independent Validation, Greedy Baselines & Simulation (`src/baselines/`, `src/evaluation/`, `src/simulation/`, `experiments/`). Branch: `features/nidhi-validation-simulation`.

*The frontend is handled by external teammates and is outside the implementation scope of these three workstreams.*

---

## 2. Deferred Per-Person Planning Workflow

> [!IMPORTANT]
> **Do not create generic checklist files at the repository root.**
> When beginning implementation on your feature branch, you must:
> 1. Read `ARCHITECTURE.md`, `PHASES.md`, `ROADMAP.md`, `REQUIREMENTS.md`, and your ownership file (`<Name>.md`).
> 2. Create your personal implementation phase plan: `PHASES_<NAME>.md` (e.g. `PHASES_LAKSHAY.md`).
> 3. Create your living task audit checklist: `CHECKLIST_<NAME>.md` (e.g. `CHECKLIST_LAKSHAY.md`).
> 4. Derive all sub-tasks directly from the approved master documents without altering architectural boundaries.

---

## 3. Branching Strategy & Git Hygiene

- **Protected Main:** The `main` branch contains verified, peer-reviewed, and tested releases. Direct unreviewed commits to `main` are strictly prohibited.
- **Dedicated Feature Branches:**
  - `features/lakshay-optimization-ml`
  - `features/nakshatra-data-state`
  - `features/nidhi-validation-simulation`
- **Zero Cross-Owner Modification:** Do not modify another lead's source modules without explicit coordination.
- **Commit Messages:** Follow Conventional Commits format:
  ```
  <type>(<scope>): <concise present-tense description>

  [detailed body explaining rationale, verification evidence, and issue references]
  ```
  Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`.

---

## 4. Code Standards & Static Analysis

### Python (Backend, ML & Solvers)
- **Runtime:** Python 3.11+
- **Linter & Formatter:** [Ruff](https://docs.astral.sh/ruff/) (Line length: 100 characters).
- **Type Checking:** [mypy](https://mypy-lang.org/) in standard/strict mode.
- **Data Schemas:** All domain models use Pydantic v2 `BaseModel` with explicit physical units in field names.

```bash
# Format and lint check:
ruff check .
ruff format --check .

# Type checking:
mypy src
```

---

## 5. Testing & Quality Gate Enforcement

No phase may be marked complete in `COMPLETION.md` without automated test evidence:
- **Unit Tests:** Fast, isolated tests targeting single modules, schemas, or constraints.
- **Independent Feasibility Audit:** Every candidate schedule must pass Nidhi's `FeasibilityAuditor` with zero hard-constraint violations.
- **Temporal Leakage Tests:** Feature extraction code must pass automated leakage tests asserting zero future timestamps.
- **Reproducibility Checks:** Generators and solvers must output identical results when supplied with documented seeds.

```bash
# Execute test suite:
pytest -v --cov=src --cov-report=term-missing
```

---

## 6. Zero-Contamination & Data Ingestion Protocols

> [!CAUTION]
> **Strict Operational Security Policy:**
> 1. **No Classified or Real Military Data:** Never introduce real-world operational logs, tactical weapon envelopes, or classified flight schedules to this repository. All core data is procedurally generated.
> 2. **Generic Nomenclature:** Use neutral identifiers (`Airbase Alpha`, `Aircraft AC-101`, `Task TASK-0042`).
> 3. **Secret Hygiene:** Never commit `.env` files, API keys, or private certificates. Ensure `.gitignore` remains active.
> 4. **Safe Ingestion Guard:** External benchmark files must not exceed 50 MB and must be verified against documented SHA-256 hashes.
