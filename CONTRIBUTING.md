# Contributing to AIRWISE

Thank you for contributing to **AIRWISE (AI-Enabled Dynamic Air Operations & Resource Optimisation)**. This project adheres to disciplined engineering practices to ensure technical credibility, reproducibility, and safety.

---

## 1. Governance & Implementation Process

All development work is organized by phases as defined in [PHASES.md](PHASES.md) and tracked in [COMPLETION.md](COMPLETION.md).

### The Engineering Workflow
1. **Identify the Next Task:** Review [COMPLETION.md](COMPLETION.md) to locate the earliest uncompleted task in the current phase.
2. **Review Specifications:** Cross-reference [ARCHITECTURE.md](ARCHITECTURE.md), [REQUIREMENTS.md](REQUIREMENTS.md), and [DECISIONS.md](DECISIONS.md) before writing code.
3. **Implement Incrementally:** Keep changes cohesive and minimal. Avoid sweeping refactors or premature multi-phase implementations.
4. **Author Automated Tests:** Every new module or schema requires automated unit tests verifying both happy paths and edge cases.
5. **Update Task Tracking:** Update [COMPLETION.md](COMPLETION.md) with the verified status and verification evidence.

---

## 2. Branching & Commit Conventions

### Branch Strategy
- `main`: Production-ready, stable, and verified branch. All code on `main` must pass all tests.
- Feature branches: `feat/<phase-id>-<short-description>` (e.g. `feat/phase-1-domain-schemas`)
- Fix branches: `fix/<issue-id>-<short-description>`

### Commit Message Guidelines
Commits follow Conventional Commits formatting:
```
<type>(<scope>): <concise present-tense description>

[optional detailed body explaining rationale and verification]
```

Types:
- `feat`: A new feature or capability.
- `fix`: A bug fix.
- `docs`: Documentation creation or updates.
- `test`: Adding or updating automated tests.
- `refactor`: Code restructuring without functional changes.
- `chore`: Tooling, configuration, or dependency updates.

Example:
```
feat(domain): implement Pydantic v2 schemas for aircraft and crew

- Add Aircraft, AirframeType, and CrewMember models
- Add interval validation logic to OperationalTask
- Verify with 14 unit tests in test_domain_models.py
```

---

## 3. Code Style & Quality Standards

### Python (Backend & Algorithms)
- **Runtime:** Python 3.11+
- **Linter & Formatter:** [Ruff](https://docs.astral.sh/ruff/)
  - Line length: 100 characters.
  - Strict docstrings on all public functions, classes, and methods.
- **Type Checking:** [mypy](https://mypy-lang.org/) in strict/standard mode.
- **Data Models:** Use Pydantic v2 `BaseModel` for validation, schemas, and API boundaries.

```bash
# Format and lint check:
ruff check .
ruff format --check .

# Type checking:
mypy src
```

### TypeScript / React (Frontend)
- **Runtime:** Node.js 18.x or 20.x LTS
- **Build Tool:** Vite
- **Linter:** ESLint with TypeScript rules.
- **Styling:** Tailwind CSS utility classes.

```bash
cd frontend
npm run lint
npm run build
```

---

## 4. Testing & Verification Standards

No task may be marked `VERIFIED COMPLETE` in [COMPLETION.md](COMPLETION.md) without passing test evidence.

- **Unit Tests:** Fast, isolated tests targeting single functions, constraints, or schemas.
- **Integration Tests:** Verifying API routes, database persistence, and end-to-end solver pipelines.
- **Reproducibility Assertion:** Optimizers and generators must be tested against fixed seeds with expected output assertions.

```bash
# Execute test suite:
pytest -v --cov=src --cov-report=term-missing
```

---

## 5. Synthetic Operational Data & Secret Hygiene Rules

> [!CAUTION]
> **Zero-Contamination Protocol:**
> 1. **No Real Military / Classified Data:** Under no circumstances should real-world operational flight logs, tactical battle-management plans, proprietary military hardware specifications, or real personnel records be introduced to this repository.
> 2. **Generic Nomenclature:** Use neutral identifiers (e.g. `Airbase Alpha`, `Aircraft AC-101`, `Sortie S-04`, `Airframe Type Transport-Heavy`).
> 3. **Secret Hygiene:** Never commit `.env`, API keys, private certificates, or local database files. Ensure `.gitignore` remains respected at all times.

---

## 6. Pull Request & Review Checklist

Before requesting review or merging to `main`:
- [ ] Task is documented in [PHASES.md](PHASES.md) and mapped in [COMPLETION.md](COMPLETION.md).
- [ ] Code strictly adheres to [ARCHITECTURE.md](ARCHITECTURE.md) component boundaries.
- [ ] All new logic is covered by unit tests.
- [ ] Linter checks pass (`ruff check`, `mypy`).
- [ ] No hardcoded secrets or sensitive operational data are present.
- [ ] All markdown links and references resolve correctly.
