# Quont Sandbox — AI Agent Guide

## 1. Purpose

This file defines mandatory working rules for AI coding agents such as Codex and Claude.

Agents must preserve the architecture rather than optimize only for short-term implementation speed.

## 2. Source-of-Truth Priority

Use the following priority order:

1. current explicit task specification,
2. current module requirements,
3. `docs/ARCHITECTURE.md`,
4. `docs/AGENTS.md`,
5. `docs/REQUIREMENTS.md`,
6. existing code conventions.

A task does not silently override architecture rules.

If the requested implementation conflicts with architecture, report the conflict before making an architectural change.

## 3. Architecture Conflict Rule

If a requested task appears to require an architecture change, state:

- current architecture rule,
- why the task conflicts,
- proposed change,
- expected consequences.

Do not silently bypass the architecture because a shortcut is easier.

## 4. Scope Discipline

Each implementation task should have one clear technical/fachlich goal.

Prefer:

- one feature,
- one coherent change set,
- relevant tests,
- relevant documentation.

Avoid broad unrelated refactors.

Do not rename, move, reformat or replace unrelated parts of the codebase without explicit need.

## 5. Local Changes

Keep modifications as local as possible.

Avoid typical oversized AI changes such as:

- deleting/replacing large working modules unnecessarily,
- mass renaming,
- global formatting unrelated files,
- replacing the logging stack,
- upgrading unrelated dependencies,
- implementing multiple future modules early.

## 6. No Premature Scaffolding

Only create directories/modules required for the current implementation phase.

The long-term architecture is documented in `ARCHITECTURE.md`.

Do not create large trees of empty modules for future functionality.

## 7. Dependency Boundaries

Respect module dependency direction.

Low-level modules must not import higher-level modules.

Do not introduce circular dependencies.

Cross-module use should go through documented public APIs.

Do not import deep internal infrastructure code from another module.

## 8. Business Logic Placement

Do not place business logic in:

- CLI handlers,
- FastAPI routes,
- SQLAlchemy ORM models,
- provider adapters,
- configuration files.

Use domain functions and application services.

The CLI may:

- parse input,
- call application services,
- display output,
- set exit codes.

It may not perform SQL queries, provider requests, return calculations or business rules directly.

## 9. Database Access

Normal application modules must not execute direct SQL.

Use repository interfaces and infrastructure implementations.

Persistent schema changes require Alembic migrations.

Do not solve schema changes by instructing the user to delete/recreate the database unless the task explicitly defines the database as disposable.

## 10. Provider Separation

Keep provider/API logic behind provider interfaces/adapters.

Keep trading venue separate from provider identity.

Provider-specific names, frequency strings and response schemas must be translated into canonical internal representations.

Do not leak provider schemas into research modules.

## 11. Data Integrity

Never silently:

- replace missing values with zero,
- drop suspicious rows,
- coerce invalid observations,
- mix adjusted and unadjusted prices,
- ignore timezone semantics,
- overwrite revised provider data without lineage.

Explicit policies and metadata are required.

## 12. Point-in-Time Safety

Do not introduce look-ahead bias.

Any data selection for research/backtesting must respect availability/publication semantics where relevant.

Do not replace historical universe membership with current membership when historical membership is required.

## 13. Run Reproducibility

Completed experiment/backtest runs are immutable.

Configuration changes create new runs.

For stochastic methods, use and record explicit random seeds where possible.

Preserve data/config/code identifiers needed for reproducibility.

## 14. Long-Running Operations

For long/batch processes:

- use run IDs,
- aggregate errors,
- support configured fallbacks,
- checkpoint resumable state,
- keep permanent run history,
- remove temporary checkpoints after successful completion.

Do not fail an entire batch for a recoverable single-item provider failure unless consistency requires aborting.

## 15. Testing Requirements

Every implementation must include appropriate tests.

Use:

- unit tests,
- synthetic/reference tests,
- integration tests,
- database tests,
- provider tests,
- e2e smoke tests.

For mathematical/transformation methods, add deterministic synthetic tests with known expected results whenever feasible.

Do not depend on live external APIs in normal test runs.

Live provider tests must be explicitly marked and opt-in.

## 16. Golden Test Data

Small deterministic fixtures may be stored under `tests/fixtures/`.

Do not commit real research datasets.

Golden datasets should be small, understandable and stable.

## 17. Definition of Done

A task is not complete until applicable items are satisfied:

- implementation complete,
- tests added/updated,
- tests pass,
- Ruff checks pass,
- formatting check passes,
- Pyright passes,
- documentation updated,
- migrations added for persistent schema changes,
- synthetic/reference test added when mathematically appropriate,
- no known architecture violation remains.

Typical checks:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

## 18. Dependencies

Do not add a new dependency merely for convenience.

Before adding one:

1. verify the standard library and existing dependencies are insufficient,
2. choose an established maintained package,
3. add it to `pyproject.toml`,
4. update the lockfile,
5. document/justify the need when material.

## 19. Language and Naming

Use English for:

- source code,
- identifiers,
- docstrings,
- project documentation,
- configuration keys,
- commit messages.

Use clear specific names.

Avoid generic containers such as `DataObject`, `Helper`, `Manager` or giant `utils.py` modules when a domain-specific name is available.

## 20. `common` Policy

`common` must remain small.

Acceptable shared concerns may include:

- core types,
- base exceptions,
- protocols,
- generic time utilities.

Domain-specific logic belongs to the owning module.

Do not turn `common` into a dumping ground.

## 21. DataFrame Contracts

Pandas/NumPy are allowed and expected in research code.

At important module boundaries, do not pass undocumented arbitrary DataFrames.

Define/validate required schema semantics where needed:

- columns,
- index,
- units,
- frequency,
- timezone,
- adjustment state.

## 22. Domain vs ORM

Do not couple domain objects directly to SQLAlchemy.

Map between domain and ORM/database representations in the infrastructure/data-access layer.

## 23. Git Behavior

AI agents may create local commits when requested or when the task workflow explicitly permits it.

AI agents must never push to GitHub automatically.

The user owns the push step.

`main` should remain runnable.

## 24. Commit Quality

Prefer small coherent commits.

A good agent task/commit should usually contain:

- one feature or bugfix,
- its tests,
- necessary documentation,
- required migration if applicable.

Avoid huge mixed-purpose commits.

## 25. Documentation

When behavior, public interfaces, architecture or module contracts change, update the corresponding documentation in the same task.

For architecture decisions with long-term consequences, add or update an ADR.

## 26. CLI Discovery

All public CLI commands and combinations must be discoverable through the central Typer CLI and help output.

Users should not need to inspect source modules or individual argument parsers to learn available commands.

## 27. Anti-Overengineering

Do not implement patterns merely because they are fashionable.

A pure mathematical function may remain a pure function.

Introduce ports, repositories, services and adapters where there is a real system boundary or substitution/testing need.

Prefer simple, explicit and testable code.
