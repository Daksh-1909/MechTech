# Phase 3 Completion Report

**Status:** Complete for the local synthetic-data prototype  
**Completed:** 2026-11-05  
**Milestone commits:** 3.0 through 3.9, listed in the repository history

## Delivered pipeline

The repository now has deterministic five-scenario dataset generation, one
versioned sensor contract, authenticated and idempotent ingestion, UTC raw
reading storage, versioned feature windows, an explainable statistical
baseline, run-separated Isolation Forest and Random Forest trainers, and a
unified API analysis path. Predictions preserve references to their immutable
source window, source readings, model versions and detector evidence. Training
artifacts are checksummed and stored under `DATA_ROOT/models`; activation is an
explicit admin action.

The local API accepts readings through `POST /api/v1/readings` and
`POST /api/v1/readings/batch`. `POST /api/v1/equipment/{equipment_id}/analysis`
persists an advisory prediction and evidence. Prediction and anomaly histories
are paginated. Admins can queue one local training job at a time with
`POST /api/v1/train` and poll it at `GET /api/v1/training-jobs/{job_id}`.
Training jobs are bounded, run in a single worker thread, register models
inactive, and expose safe failure text rather than exception details.

## Verification

Final verification on Windows 11, Python 3.13.7:

- `python -m pytest -p no:cacheprovider backend -q`: **98 passed**.
- `ruff check backend simulator`: passed.
- `ruff format --check backend simulator`: **152 files formatted**.
- Fresh-database Alembic upgrade is included in the test suite and passed.
- Integration path: 50 deterministic simulator contract readings persisted
  through the versioned batch API, then analysis generated a stored prediction
  linked to its source window and readings.
- Random Forest CLI training: two training runs and one held-out run, 40
  samples per scenario; accuracy and macro F1 were both 1.0 on this small
  synthetic test partition.
- Isolation Forest CLI training: two training runs and one separate evaluation
  run, 40 samples per scenario; F1 0.9153, abnormal detection 96.43%, and
  false-positive rate on normal windows 57.14% (7 normal evaluation windows).
- Statistical baseline smoke run: 7/7 normal windows unflagged and 7/7 windows
  from each abnormal scenario flagged at the configured experimental rule.
- Bounded dataset/feature benchmark: 2 runs × 40 samples per scenario produced
  70 windows in about **0.21–0.22 seconds**, with an approximately **0.87 MB**
  Python traced allocation peak on this machine. This is a local sample, not a
  production capacity claim.
- The existing API benchmark and test coverage exercise persistence, bounded
  query inputs, authorization, and history pagination. The ML benchmark above
  focuses on CPU/memory cost of generation and feature extraction; it does not
  claim a database load benchmark.

One Starlette/httpx deprecation warning remains from the installed test-client
dependency. It does not fail tests and is not caused by Phase 3 code.

## Model and data limits

All Phase 3 training/evaluation data is deterministic synthetic data. The
perfect small-partition Random Forest result is not evidence of field accuracy.
The Isolation Forest result demonstrates why false-positive rate must be
reported alongside detection rate. Vibration values produced by the simulator
are a simplified `simulated_index`, not calibrated mm/s RMS measurements.
Neither model provides certified diagnosis, a safety limit, or control
instructions. Predictions are advisory and require human review.

The SQLite deployment is intended for a single local API process. The
single-worker training queue is process-local and is not a distributed job
system; do not run multiple API worker processes against it. No automatic
retention deletion is performed. Raw waveform/frequency analysis is not
supported by the RMS-style simulator channel.

## Phase 4 prerequisites

Before connecting physical equipment or presenting diagnosis as validated:

1. Agree on calibrated sensor units, device identity, authentication/key
   rotation, clock synchronization, and a hardware payload profile.
2. Collect representative labeled real motor data and obtain domain review of
   fault labels and safe operational thresholds.
3. Define validation splits by equipment/site/time, confidence calibration,
   alert review workflow, monitoring and retraining policy.
4. Re-evaluate storage and background-job architecture if concurrency exceeds
   the local single-process SQLite prototype.
5. Add waveform contracts only for sensors that actually provide raw
   waveforms, then evaluate frequency-domain processing separately.

## Error log

Actionable implementation and verification failures and their resolutions are
recorded in [`phase-3-error-log.md`](phase-3-error-log.md).
