# Quont Sandbox — Requirements

## 1. Vision

Quont Sandbox is a local-first quantitative research and strategy platform.

The long-term purpose is to maintain a central, auditable research database containing market prices, quotes, returns, characteristics, factors, macroeconomic data, corporate actions and derived data. Multiple independent research capabilities shall access this common data platform.

The platform shall eventually support:

- quantitative research,
- asset pricing,
- forecasting,
- machine learning,
- signal generation,
- portfolio construction,
- strategy definition,
- backtesting,
- evaluation and reporting.

The first development phase is intentionally narrower: build a reliable Data Platform first.

## 2. Initial Operating Model

- Single-user application for the first development phases.
- Local execution on the user's computer.
- Local PostgreSQL database.
- No hosting requirement for the initial version.
- No UI requirement for the initial version.
- The primary user interface is a CLI.
- Future FastAPI and React interfaces must reuse the same application core rather than duplicate business logic.
- Live trading and broker execution are explicitly out of scope for the initial versions.

## 3. Initial Asset Classes

Version 1 shall support:

- equities,
- ETFs,
- cryptocurrencies.

The architecture must remain extensible to additional asset classes such as FX, bonds, futures, options, commodities and indices.

## 4. Supported Data Frequencies

The platform shall support multiple frequencies in parallel, including:

- intraday,
- daily,
- monthly.

Frequencies must be standardized internally and must not depend on provider-specific naming.

True timestamps and calendar/trading periods must be represented separately where appropriate.

## 5. Central Data Platform

External providers and files are ingestion sources. Research modules should normally consume canonical internal datasets rather than call external APIs directly.

The conceptual data flow is:

External Source
→ Raw Storage
→ Validation
→ Normalization
→ Canonical Store
→ Derived Data
→ Dataset Access Layer
→ Research / Models / Backtests

## 6. Persistent Data Categories

The platform shall eventually support at least:

- asset metadata,
- instruments and listings,
- trading venues,
- identifiers,
- OHLCV bars,
- quote data,
- returns,
- corporate actions,
- fundamentals,
- characteristics,
- factors,
- macroeconomic series,
- derived features,
- provider metadata,
- import/update run metadata,
- data lineage,
- data quality results.

## 7. Raw Data

Raw provider responses and imported source files shall be retained where feasible.

Raw data exists for:

- auditability,
- reproducibility,
- debugging,
- reprocessing without another external download,
- comparison between provider revisions,
- preservation of source evidence.

Large raw payloads may be stored in the local filesystem rather than directly inside PostgreSQL. PostgreSQL should retain metadata such as file identity, provider, acquisition timestamp, checksum and storage location.

## 8. Data Lineage and Versioning

The system shall record sufficient lineage to understand where canonical data came from and how it was transformed.

Important metadata includes:

- source/provider,
- provider-specific identifier,
- venue where relevant,
- acquisition timestamp,
- import/update run,
- source raw artifact,
- processing timestamp,
- transformation/normalization version,
- detection of changed provider values.

Provider revisions must not be silently indistinguishable from original values.

## 9. Point-in-Time Data

The architecture shall support point-in-time correctness.

Data may carry fields such as:

- observation date/time,
- publication date/time,
- available-from date/time.

Research, forecasting and backtesting modules must not use information that was unavailable at the simulated point in time.

## 10. Asset Identity

Internal asset identity must not depend on mutable external tickers.

The model shall support stable internal IDs and separate external identifiers such as:

- ticker,
- ISIN,
- FIGI,
- CUSIP,
- exchange symbol,
- provider ID,
- crypto symbol.

Asset, instrument/listing and trading venue are distinct concepts.

## 11. Venue and Provider Hierarchy

The system shall support configurable fallback routing.

For a requested dataset, routing may consider:

- data type,
- asset class,
- asset/instrument,
- provider/API,
- trading venue,
- quote currency,
- frequency.

A request may therefore fall back across both provider/API and venue combinations.

Example:

1. Provider A / Binance
2. Provider A / Coinbase
3. Provider B / Binance
4. Provider B / Coinbase

The routing hierarchy must be configurable and must not be embedded in research code.

## 12. Market Data Types

### 12.1 Bars

Bar data shall support at least:

- open,
- high,
- low,
- close,
- volume.

### 12.2 Quotes

Quote data shall be modeled separately from bars and may include:

- bid price,
- ask price,
- bid size,
- ask size,
- timestamp,
- venue.

Quotes are especially relevant for later transaction-cost and execution-aware backtesting.

### 12.3 Trades

The architecture may later support trade-level observations separately from bars and quotes.

## 13. Adjusted Prices

Adjusted and unadjusted prices must never be mixed without explicit metadata.

The exact policy remains an open architecture decision:

- provider-adjusted prices,
- internally adjusted prices from corporate actions,
- or both as separate explicit series.

## 14. Corporate Actions

Corporate actions belong to the initial data model.

At minimum:

- stock splits,
- cash dividends.

The model must be extensible to additional event types.

## 15. Returns

Returns shall be stored as derived datasets while raw/canonical prices remain available.

When appropriate, returns shall be generated automatically after market-data ingestion or updates.

Return metadata shall identify at least:

- source price series,
- frequency,
- adjustment policy,
- return methodology,
- processing version.

## 16. Characteristics and Derived Features

The platform must distinguish externally supplied characteristics from internally computed characteristics/features.

Internal derivations should retain lineage to:

- input datasets,
- calculation method,
- parameters,
- calculation version,
- calculation timestamp.

## 17. Macroeconomic Data

Macroeconomic series belong to the same Data Platform but are not modeled as artificial assets.

Macro series shall use their own stable series identity.

Examples:

- CPI,
- inflation,
- policy rates,
- unemployment,
- GDP,
- yield series.

## 18. Supported Ingestion Types

Initial ingestion shall support:

- API/Python providers,
- CSV,
- XLSX,
- XML.

Additional file formats should be easy to add.

Provider/file-specific schemas must be normalized before they reach downstream research modules.

## 19. Database

PostgreSQL is the primary relational database.

Database schema evolution shall be managed through migrations.

Raw files and disposable caches may live outside PostgreSQL.

## 20. Initial Scale

The first goal is correctness rather than maximum scale.

An initial validation universe may contain roughly:

- about 50 equities,
- selected ETFs,
- selected cryptocurrencies,
- multiple frequencies.

Once the full ingestion/update/audit path is validated, larger universes can be downloaded in batches.

## 21. Incremental Updates

The system must detect already stored coverage and request only missing/new data when possible.

The update process should determine:

- existing coverage,
- current expected/provider coverage,
- missing ranges,
- update ranges,
- relevant source/provider route.

Full re-downloads should require explicit justification or instruction.

## 22. Scheduler

An optional scheduler shall be supported later.

Initial behavior:

- scheduler exists conceptually but is disabled by default,
- all update operations must be runnable manually through the CLI,
- scheduler code must call the same application services as the CLI.

## 23. Jobs, Batching and Checkpointing

Long-running operations shall be represented as runs/jobs.

A run may record:

- run ID,
- status,
- start/end timestamps,
- progress,
- batch position,
- processed items,
- failures,
- warnings.

Large workloads shall support batching.

Checkpointing shall support safe resume after interruption.

Checkpoints are temporary recovery state and shall be removed after a successful full run.

Permanent run history shall remain.

## 24. Error Handling and Fallbacks

A failure on one asset should not necessarily abort a whole batch.

Expected behavior for recoverable errors:

- record error,
- attempt configured provider/venue fallbacks,
- continue with remaining items,
- produce final success/failure summary.

Critical consistency/database failures may abort the run.

## 25. Data Quality

Imports and updates shall support automated quality checks, including where applicable:

- duplicates,
- missing observations,
- gaps,
- invalid timestamps,
- invalid data types,
- impossible prices,
- invalid volume,
- unexpected frequency,
- suspicious outliers,
- inconsistencies with existing data.

Quality checks should produce persistent reports.

Critical errors may block promotion into the canonical store.

## 26. Reproducibility

Research and backtest results should remain reconstructable years later.

Run metadata should be capable of recording:

- dataset/data version,
- universe,
- time period,
- frequency,
- model/strategy version,
- parameters/hyperparameters,
- features,
- benchmark,
- cost assumptions,
- random seed,
- execution time,
- code/software version.

Completed research/backtest runs are immutable.

Changing parameters creates a new run.

## 27. Experiment Registry

The platform shall support persistent experiment specifications and immutable experiment runs.

Experiments may describe:

- research question,
- universe,
- dataset,
- method/model,
- target,
- inputs/features,
- period,
- configuration,
- results,
- diagnostics.

## 28. Research Scope

The long-term research layer shall support reusable statistical and numerical methods that can be consumed by higher-level modules.

Examples:

- regressions,
- regularization,
- PCA,
- IPCA,
- statistical tests,
- resampling,
- optimization.

General methods should not be duplicated separately inside every economic application module.

## 29. Higher-Level Modules

Long-term modules include:

- asset pricing,
- forecasting,
- signals,
- portfolio construction,
- strategies,
- backtesting,
- experiments,
- reporting.

These modules shall all consume the common data platform through defined interfaces.

## 30. Testing Requirements

Testing is a core product requirement.

The project shall use:

- unit tests,
- synthetic/reference tests,
- integration tests,
- database tests,
- provider tests,
- end-to-end smoke tests.

Mathematical and transformation methods should use synthetic datasets with known expected results whenever feasible.

Small version-controlled golden datasets shall support reproducible pipeline tests.

Live external provider tests must be explicitly marked and excluded from normal test runs.

## 31. Current Development Priority

The first implementation milestone is the Data Platform.

It is successful when the system can reliably:

1. define assets/instruments/venues,
2. ingest from supported sources,
3. retain raw source data,
4. validate and normalize data,
5. store canonical data,
6. compute/store required derived returns,
7. report data coverage,
8. perform incremental updates,
9. route across configured provider/venue fallbacks,
10. batch and checkpoint long-running jobs,
11. audit data quality,
12. expose clean access interfaces to future research modules.
