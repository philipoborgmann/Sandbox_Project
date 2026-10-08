# Quont Sandbox — Architecture

## 1. Architecture Goal

Quont Sandbox is implemented as a modular Python monolith in a single Git repository.

The project deliberately avoids microservices during the local-first research phase.

The architecture must make future interfaces possible without rewriting the core:

CLI
→ Application Core ← FastAPI (later)
                 ← React/Web UI (later)

The CLI, future API and future UI are adapters. They must not own business logic.

## 2. Repository Layout

Target top-level layout:

```text
quont-sandbox/
├── src/
│   └── quont_sandbox/
├── tests/
├── docs/
├── config/
├── scripts/
├── notebooks/
├── data/
├── migrations/
├── pyproject.toml
├── uv.lock
├── README.md
└── .gitignore
```

Only modules required by the current implementation phase should be physically created.

The long-term architecture is documented here but empty placeholder trees should be avoided.

## 3. Package Name and CLI

Project name:

`Quont Sandbox`

Python package:

`quont_sandbox`

Primary CLI command:

`quont`

Examples:

```bash
quont data import
quont data update
quont data audit
quont assets list
quont experiments run
quont backtest run
```

The CLI framework shall be Typer.

A central CLI command registry shall expose available commands and subcommands so users do not need to inspect individual modules to discover parser options.

## 4. Long-Term Module Boundaries

Conceptual modules:

```text
data
assets
research
asset_pricing
forecasting
signals
portfolio
strategies
backtesting
experiments
reporting
common
```

Not all modules are created immediately.

### `assets`

Owns identity and reference data:

- Asset
- Instrument / Listing
- Venue
- Identifier
- historical universe membership

### `data`

Owns data acquisition and time-series/data management:

- bars
- quotes
- returns
- corporate actions
- characteristics
- macro series
- raw ingestion
- updates
- validation
- lineage
- quality checks

### `research`

Owns reusable mathematical/statistical methods.

Higher-level economic modules use `research`; the reverse dependency is not allowed.

## 5. Dependency Direction

Low-level modules must not depend on higher-level business modules.

Conceptual dependency direction:

```text
assets/data/common
        ↓
     research
        ↓
asset_pricing / forecasting
        ↓
      signals
        ↓
portfolio / strategies
        ↓
    backtesting
```

This is an allowed dependency direction, not a mandatory runtime pipeline.

Circular module dependencies are architecture violations.

## 6. Layering Principle

The system follows pragmatic Clean Architecture / Ports-and-Adapters principles.

Conceptually:

```text
CLI / future API
       ↓
Application Services
       ↓
Domain/Core
       ↓
Ports / Interfaces
       ↑
Infrastructure Adapters
       ↓
PostgreSQL / APIs / Files
```

This principle is mandatory at real system boundaries but must not create unnecessary boilerplate for simple pure functions.

A mathematical function such as `annualized_return()` may remain a simple pure function.

A workflow that performs API calls, database reads/writes, batching, validation and retries must be orchestrated through application services and adapters.

## 7. Domain Independence

Domain models must not depend on:

- SQLAlchemy,
- Typer,
- FastAPI,
- provider SDKs,
- filesystem implementation details.

Domain model and ORM/database model are separate concepts.

Example:

`Asset` domain object

is not the same class as:

`AssetRow` SQLAlchemy model.

## 8. Application Services

Application services represent use cases.

Examples:

- ImportMarketData
- UpdateMarketData
- CalculateReturns
- RunDataAudit
- CreateAsset
- RunExperiment
- RunBacktest

Application services orchestrate repositories, providers, validation, run/checkpoint services and domain functions.

They do not contain UI concerns.

## 9. Infrastructure Adapters

Infrastructure contains concrete external integrations such as:

- PostgreSQL / SQLAlchemy,
- API providers,
- CSV/XLSX/XML importers,
- local raw-file storage,
- cache storage,
- logging sinks.

Provider-specific data structures must be translated into canonical internal models before reaching downstream modules.

## 10. Repositories

Repository interfaces are defined at the application/domain boundary.

Naming examples:

- AssetRepository
- MarketDataRepository
- ExperimentRepository
- RunRepository

Concrete adapters:

- PostgresAssetRepository
- PostgresMarketDataRepository

Tests may use:

- InMemoryAssetRepository
- FakeMarketDataRepository

Normal application modules must not execute direct SQL.

## 11. Public Module APIs

Modules expose explicit public interfaces.

Preferred:

```python
from quont_sandbox.data import MarketDataRequest
```

Avoid cross-module imports from deep internal infrastructure paths.

Internal module refactoring should not break other modules when the public API remains stable.

## 12. DTOs and Schemas

Important application boundaries shall use explicit request/result/schema types.

Naming examples:

- CreateAssetRequest
- CreateAssetResult
- MarketDataRequest
- MarketDataResult
- BacktestRequest
- BacktestResult

Pydantic is the default schema/validation library for application boundary objects.

Pydantic is not required for every numerical inner-loop object.

## 13. DataFrame Policy

Pandas is the default dataframe library for the initial versions.

NumPy and Pandas are appropriate within numerical/research code.

Important system boundaries should not rely on undocumented arbitrary dataframe shapes.

Where necessary, schemas/contracts must define:

- required columns,
- index semantics,
- frequency,
- adjustment status,
- units,
- timezone rules.

The architecture should not make future targeted use of Polars impossible.

## 14. IDs

Stable internal IDs shall be separate from human/provider identifiers.

Examples:

- asset_id,
- instrument_id,
- venue_id,
- provider_id,
- dataset_id,
- experiment_id,
- run_id,
- strategy_id,
- backtest_id.

Ticker and names are attributes, not primary identity.

UUIDs are preferred for externally stable technical identities; database implementation may use UUID and/or bigint where justified, but business logic must never rely on sequential numbering.

## 15. Provider and Venue

Provider and venue are distinct:

- Provider = who supplies the data.
- Venue = where the market activity occurred.

Provider routing may combine both concepts.

A provider/API fallback layer shall exist above venue selection so the system can change provider entirely when a source cannot supply a requested dataset.

## 16. Frequency

Frequency uses centralized controlled values rather than arbitrary strings.

Initial examples:

- 1m
- 5m
- 1h
- 1d
- 1mo

Provider adapters translate provider-specific frequency names to canonical values.

## 17. Asset Classes

Initial controlled values:

- EQUITY
- ETF
- CRYPTO

The design must permit later extension.

## 18. Time Semantics

All true timestamps are timezone-aware.

UTC is the internal default for event timestamps.

PostgreSQL timestamps should use timezone-aware storage where applicable.

Do not force all temporal concepts into timestamps.

Examples:

- intraday observations: timestamp,
- daily observations: trading_date plus optional market-close timestamp,
- monthly observations: explicit period / period-end semantics.

Exchange/local timezone is retained as metadata where required.

## 19. Numerical Precision

Research/numerical computation normally uses float64.

Exact monetary/fee calculations may use Decimal where exact decimal arithmetic is required.

Do not use Decimal indiscriminately in numerical/ML pipelines.

## 20. Missing Values

Missing values must never be silently converted to zero.

Any imputation/fill policy must be explicit and, for research runs, reproducibly recorded.

## 21. Bias Controls

### Look-ahead bias

No research, forecasting or backtesting component may use information unavailable at the simulated time.

### Survivorship bias

The architecture supports historical universe membership with validity intervals such as:

- valid_from,
- valid_to.

## 22. Immutable Runs

Completed experiment and backtest runs are immutable.

Changing configuration creates a new run.

Run history is permanent audit information.

Checkpoint data is temporary recovery state.

## 23. Randomness

Stochastic processes shall use explicit random seeds where technically possible.

Seeds must be recorded for reproducible experiment/backtest runs.

## 24. Long-Running Jobs

Long processes are modeled as jobs/runs.

They support:

- batching,
- progress,
- error aggregation,
- retries,
- provider/venue fallback,
- checkpointing,
- resume.

A successful completed run deletes its temporary checkpoints but retains its run history.

## 25. PostgreSQL and Migrations

PostgreSQL is the primary relational database.

SQLAlchemy is the intended ORM/data-access technology.

Alembic manages schema migrations.

Every persistent schema change requires a migration.

Agents must not replace migrations with ad-hoc destructive database recreation.

## 26. Raw, Cache and Export Storage

Local project data layout:

```text
data/
├── raw/
├── cache/
└── exports/
```

`raw/`:
source evidence; not automatically disposable.

`cache/`:
derived temporary data; may be deleted and rebuilt.

`exports/`:
user-created output artifacts.

This project-level `data/` directory contains data files.

It is different from:

`src/quont_sandbox/data/`

which contains Python source code for data acquisition, validation, transformation, persistence and access.

## 27. Git Data Policy

Real research datasets are not committed.

Typical `.gitignore` exclusions:

- data/raw/
- data/cache/
- data/exports/
- .env
- logs/

Small deterministic test fixtures may be committed under:

`tests/fixtures/`

## 28. Configuration

Configuration precedence:

Defaults
→ configuration files
→ environment variables
→ CLI arguments

Secrets belong in environment variables / `.env`, never committed configuration.

Configuration stores values and policies, not complex executable business logic.

Initial configuration structure may include:

```text
config/
├── default.yaml
├── providers.yaml
└── logging.yaml
```

Add new configuration files only when required.

## 29. Experiment and Strategy Specifications

Version-controlled declarative specifications may live in locations such as:

```text
experiments/specs/
strategies/specs/
```

A specification is distinct from an immutable executed run.

Runs store/capture configuration identity, hashes/versions and dataset/code metadata required for reproducibility.

## 30. Notebooks

Notebooks may consume the public Python API but must not contain the only production implementation of core logic.

Suggested structure:

```text
notebooks/
├── exploration/
├── validation/
└── examples/
```

## 31. Scripts

`scripts/` contains development/admin helpers only.

Acceptable examples:

- bootstrap_db.py
- generate_test_data.py

Core workflows belong behind the central CLI and application services.

Avoid one-off production workflows such as `run_backtest_final_v7.py`.

## 32. Testing Architecture

Test categories:

```text
tests/
├── unit/
├── synthetic/
├── integration/
├── database/
├── providers/
├── e2e/
└── fixtures/
```

Synthetic/reference tests are especially important for:

- regressions,
- statistics,
- return calculations,
- corporate-action adjustments,
- factor construction,
- transformations,
- optimization,
- signal logic,
- backtesting.

Live provider tests are opt-in and excluded from normal `pytest` runs.

## 33. Toolchain

Project baseline:

- Python 3.12,
- `pyproject.toml`,
- `uv`,
- Pandas,
- Pydantic,
- Typer,
- SQLAlchemy,
- Alembic,
- PostgreSQL,
- pytest,
- Ruff,
- Pyright.

`uv.lock` is committed.

New dependencies require justification and must not be added casually by agents.

## 34. Static Quality Rules

Ruff handles linting/formatting.

Pyright handles static typing.

Pytest handles executable correctness tests.

Public functions, interfaces, DTOs and services require meaningful type annotations.

Internal local variables do not require excessive annotation.

## 35. Naming

Code, documentation, docstrings, configuration keys and commit messages are written in English.

Python uses normal Python naming conventions.

PostgreSQL uses snake_case.

Table names should be plural where practical.

Examples:

- assets
- instruments
- venues
- price_bars
- quotes
- corporate_actions
- experiment_runs

## 36. Error Model

Use project-specific exception hierarchies rather than generic `Exception` for expected platform errors.

Example hierarchy:

```text
QuontSandboxError
├── DataError
│   ├── ProviderError
│   ├── ValidationError
│   └── DataNotFoundError
├── ResearchError
├── BacktestError
└── ConfigurationError
```

## 37. Logging vs Audit Trail

Logging records technical execution detail.

Audit/run metadata records durable business/research actions.

Logs may be rotated/deleted.

Run history and reproducibility metadata remain persistent.

## 38. Git Workflow

Single-developer workflow:

- `main` must remain runnable.
- use small feature branches where useful,
- run quality checks before merge,
- local commits are allowed for AI agents,
- AI agents must never push to GitHub automatically,
- the user performs `git push` manually.

## 39. Anti-Overengineering Rule

Architecture rules exist to preserve real boundaries, not to maximize abstraction.

Do not introduce extra interfaces, factories or layers when a pure function or small module is sufficient.

Prefer the simplest design that still respects module ownership, dependency direction and infrastructure separation.

## 40. Architecture Decision Records

Important architecture decisions are documented in:

`docs/adr/`

Examples:

- ADR-001-use-postgresql.md
- ADR-002-pandas-default.md
- ADR-003-separate-domain-and-orm.md

ADRs record both the decision and its rationale.
