# ADR 001: Initial foundation contracts

Status: Accepted for the initial foundation.

## Context

The root architecture requires domain/ORM separation, stable IDs, explicit time
semantics and incremental scope. It leaves specific temporal representation,
configuration format and the initial repository granularity open.

## Decisions

- Preserve the three existing source-of-truth documents at the root; add this
  implementation ADR under `docs/adr` without relocating or rewriting them.
- Use immutable, strict Pydantic domain models with UUID identities and explicit
  module exports. Construction rejects extra fields and ambiguous temporal input.
- Model observation time as exactly one UTC timestamp, trading date, or calendar
  year/month period. Intraday bars denote interval starts. Daily optional close
  timestamps and non-calendar macro periods are deferred until a concrete use case.
- Require source price series ID and adjustment policy for bars and derived returns.
  This represents separate series without choosing a corporate-action engine or
  adjustment algorithm. In-memory bars are idempotent and reject overwriting revisions.
- Initial external identifiers attach to instruments, with a namespace and a
  half-open date validity interval. Provider namespaces differ from venues.
  Identifier identity/history fields are immutable; an open interval can be closed
  once. A subsequent identifier has a new interval ID, preserving the prior row.
  Point-in-time identifier resolution and overlap policies remain future work.
- Persist only the asset hierarchy now; do not design future market-data tables.
  Catalogue ports encompass the four current entity types. Concrete SQLAlchemy
  sessions are composed outside domain/application catalogue use cases; callers
  own transactions.
- Use standard-library TOML with explicit file loading, environment variables and
  CLI overrides. Avoid an extra YAML or dotenv dependency. Defaults contain no secrets.
- Raw storage uses UUID artifact directories and SHA-256. Each acquisition is a
  separate artifact even if content matches; metadata is returned for later ingestion
  lineage persistence. Filenames are restricted to a portable safe single component.
  The local filesystem is trusted against concurrent hostile modification; resolved
  containment checks reject preexisting path traversal.
- Crossed quotes and negative prices are retained, because anomaly detection and
  asset-specific price policies belong to future data quality. Negative sizes,
  nonfinite values and impossible OHLC ranges are domain errors.

## Consequences

This is a runnable foundation with explicit contracts, not a complete Data Platform.
Persistent market-data lineage and identifier resolution require subsequent designs
and migrations. No current canonical data claims point-in-time research readiness.
PostgreSQL remains the only database target; normal tests use in-memory adapters,
DDL compilation and offline migration SQL. Opt-in database tests isolate a temporary
schema in a dedicated PostgreSQL test database.
