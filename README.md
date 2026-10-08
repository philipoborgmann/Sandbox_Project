# Quont Sandbox

A local-first quantitative research platform. This milestone provides the initial
asset catalogue and canonical data contracts, PostgreSQL persistence foundation,
CLI and raw source storage. It does not yet download or ingest market data.

The existing root documents remain the source of truth:
[Requirements](REQUIREMENTS.md), [Architecture](ARCHITECTURE.md), and [Agent guide](AGENTS.md).
Implementation choices and API contracts are in [the foundation ADR](docs/adr/001-foundation-contracts.md).

## Local development

Install `uv`, then run from the repository root:

```bash
uv sync
uv run quont --help
uv run quont --version
uv run quont assets --help
uv run quont data --help
uv run quont data paths
```

Python 3.12 is selected by `.python-version`. `uv.lock` locks dependencies.
`python -m uv` is equivalent if uv's executable directory is not on PATH.

Quality checks:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

Database and live-provider tests are opt-in, excluded from the normal suite.
No real provider adapter exists yet. Synthetic tests will accompany numerical
methods when those methods are implemented; this milestone includes no return calculator.

## Configuration and PostgreSQL

Precedence: built-in defaults → explicit TOML file → `QUONT_*` environment
variables → CLI overrides. Relative storage paths resolve from the current working
directory. `config/default.toml` documents defaults; load it with
`quont --config config/default.toml ...`. `.env.example` lists environment names;
`.env` is not loaded automatically. Settings redact database credentials.

Create a local PostgreSQL database using your usual PostgreSQL administration
tools. Export `QUONT_DATABASE_URL` with the SQLAlchemy driver form
`postgresql+psycopg://USER:PASSWORD@localhost:5432/quont`. Never commit credentials.
For example, PowerShell:

```powershell
$env:QUONT_DATABASE_URL = 'postgresql+psycopg://USER:PASSWORD@localhost:5432/quont'
uv run alembic upgrade head
uv run quont assets list
```

Alembic uses the same environment variables, and accepts a TOML path through
`QUONT_CONFIG_FILE`. Inspect migration SQL without a server:

```bash
uv run alembic upgrade head --sql
```

The first migration creates `assets`, `venues`, `instruments`, and
`external_identifiers`. Normal schema evolution uses migrations, not database
recreation. Repository callers own session commit/rollback; the adapter flushes
writes but never commits them.

To run the PostgreSQL round-trip, migration and constraint tests, set
`QUONT_TEST_DATABASE_URL` to a **dedicated test database** and run:

```bash
uv run pytest -m database
```

Tests create and drop their own UUID-named schema, without touching public tables.
The test user needs schema creation privileges. Missing test configuration skips
the test; connection/migration failures with configured credentials fail it.

## Initial public contracts

- `quont_sandbox.assets` exposes UUID-based Asset, Instrument, Venue,
  ExternalIdentifier and the catalogue repository port. A single asset can have
  multiple instruments on one or more venues. An open identifier interval can be
  closed once; later identifiers use new IDs, retaining prior history.
- `quont_sandbox.data` exposes separate bars, quotes, returns and macro series,
  provider/request ports, a minimal price repository port and raw-storage port.
  Explicit adjustment policy and source series identity prevent implicit mixing.
- Timestamps must be aware and are normalized to UTC. Daily bars use trading dates;
  monthly bars use calendar year/month periods. Intraday bar timestamps denote
  bar starts. Missing numerical values remain `None`; infinities and NaNs are invalid.
- Validation of domain schemas uses Pydantic validation errors. Expected adapter
  and configuration failures use the project's `QuontSandboxError` hierarchy.
- Raw files are written under a fresh artifact UUID, retain original bytes, and
  return SHA-256, provider ID, acquisition time, location and byte length. Store
  this returned metadata with future ingestion lineage; durable metadata persistence
  is deferred. UTF-8 is used for text. Raw files are never automatically deleted.
- Cache and exports directories cannot overlap raw storage. These local data paths
  are created only when needed and ignored by Git. Source code lives separately
  under `src/quont_sandbox/data`.

Real providers, ingestion workflows, market-data persistence, return calculation,
corporate actions, routing, quality reports, run/checkpoint history and research
modules remain for subsequent phases.
