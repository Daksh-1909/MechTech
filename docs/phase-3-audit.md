# Phase 3 Repository Audit

## Baseline reviewed

- Phase 1 requirements and Phase 2 backend architecture.
- FastAPI, SQLAlchemy 2, Alembic and SQLite backend.
- Existing authentication, equipment permissions, reading ingestion, alert and prediction APIs.
- Existing simulator client and seeded scenarios.
- Existing synthetic feature dataset, classifier training/evaluation scripts and model registry.

## Reusable implementation

Phase 2 already validates and stores readings, rejects archived equipment, deduplicates event IDs, exposes bounded reading queries, evaluates simple configured thresholds, persists anomaly/alert records, restricts inference by role, and confines model artifacts to `DATA_ROOT/models`. The simulator sends through the same HTTP ingestion API. These paths remain the compatibility baseline.

## Gaps for Phase 3

1. The Phase 2 reading contract has no schema version, sequence, operating-condition or scenario metadata.
2. Simulator runs are not reproducible as datasets: timestamps and event IDs are generated at runtime, there is no CSV export, and the required bearing-abnormality class is missing.
3. Feature extraction is a summary of an entire recent-reading list. It does not segment windows, report gaps/irregular cadence, reject incomplete windows, or calculate the specified versioned statistics.
4. Training data uses four labels and splits windows randomly, which does not meet the five-class, independent-run evaluation requirement.
5. Training currently uses Logistic Regression. There is no Isolation Forest model or persisted statistical baseline.
6. Prediction evidence lacks an explicit feature-window record, feature-window time bounds, anomaly detector output, artifact checksum and dataset/run provenance.
7. Model activation is implicit during registration; activation and long-running training do not have dedicated protected API workflows.
8. The repository has no Phase 3 runbook or error log.

## Compatibility decisions

- Preserve the Phase 2 `/readings` and `/readings/batch` API and its vibration-unit semantics.
- Add a versioned Phase 3 contract and adapt it to the existing ingestion service; extend storage additively with nullable metadata columns and a migration.
- Keep the simulator's existing API-send mode and scenario names working while adding the five Phase 3 labeled scenarios, deterministic offline generation and CSV export.
- Treat all simulator values, evaluation metrics and predictions as synthetic advisory outputs. Do not claim industrial accuracy or interpret normalized vibration as mm/s RMS.
- Use run-level splits before feature-window creation so overlapping windows from one simulation run cannot cross train/test partitions.

## Milestone execution order

Milestone 1: shared versioned payload and deterministic simulator.  
Milestone 2: adapter ingestion, metadata migration and validation.  
Milestone 3: deterministic feature windows and persistence.  
Milestone 4: explainable persisted statistical baseline.  
Milestone 5: Isolation Forest training, evaluation and inference.  
Milestone 6: Random Forest dataset/training/evaluation with run-level splits.  
Milestone 7: unified evidence and protected history/model APIs.  
Milestone 8: reliability, security and measured performance checks.  
Milestone 9: runbook, acceptance report and Phase 3 sign-off.
