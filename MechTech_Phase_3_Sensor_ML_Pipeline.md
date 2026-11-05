# MechTech --- Phase 3: Sensor Simulation, Signal Processing & Machine Learning

**Document type:** Engineering phase specification\
**Project:** MechTech --- Intelligent Equipment Monitoring and Fault
Diagnosis System\
**Phase:** 3 --- Sensor Simulation, Signal Processing & Machine
Learning\
**Status:** Development baseline\
**Primary focus:** Backend, data engineering, signal processing, machine
learning, storage, reliability and testing\
**Equipment:** Electric motor\
**Data source:** Deterministic Python sensor simulator\
**Initial database:** SQLite\
**ML framework:** Scikit-learn

------------------------------------------------------------------------

## 1. Purpose of this document

This document defines the complete Phase 3 implementation plan for
MechTech. It is intended to be supplied to an OpenAI-powered coding
assistant operating through OmniRoute, so that assistant can understand
the project's requirements and implement this phase consistently.

This is an engineering specification, not a request to begin every task
at once. Work must proceed milestone by milestone. The coding assistant
must inspect the existing repository and the Phase 1 and Phase 2
documents before changing code.

Phase 3 creates the backend intelligence pipeline that converts
simulated motor sensor readings into validated, processed data, anomaly
events, advisory fault classifications and persisted prediction
evidence.

## 2. Project context

MechTech is a local-first, zero-budget intelligent equipment monitoring
and fault diagnosis platform. Its first monitored equipment category is
an electric motor. The wider system will eventually include:

-   User registration, authentication and role-based access.
-   Equipment registration and management.
-   Temperature and vibration monitoring.
-   Abnormal-condition detection and fault classification.
-   A realistic interactive 3D motor digital twin.
-   Component-level fault highlighting.
-   Diagnostic suggestions and repair knowledge.
-   Maintenance history, alerts and equipment health trends.

The current engineering priority is the backend: APIs, database design,
storage, processing performance, security and authentication. Frontend
development, 3D implementation and deployment are later phases and must
not distract from Phase 3.

## 3. Phase 3 objective

Build a reproducible and testable sensor-to-prediction pipeline:

``` text
Deterministic Sensor Simulator
          |
          v
Sensor Data Contract
          |
          v
Validation and Ingestion
          |
          v
Raw Reading Storage
          |
          v
Signal Processing and Feature Engineering
          |
          +-----------------------+
          |                       |
          v                       v
Statistical Baseline        Feature Windows
          |                       |
          v                       v
Anomaly Detection           Fault Classification
(Isolation Forest)          (Random Forest)
          |                       |
          +-----------+-----------+
                      |
                      v
             Evidence and Confidence
                      |
                      v
          Prediction / Event Persistence
                      |
                      v
             Evaluation and Reports
```

The pipeline must be usable through Python services and FastAPI
endpoints. It must not depend on a frontend, physical sensors, cloud
services or paid APIs.

## 4. Scope

### 4.1 Included in Phase 3

1.  Deterministic electric-motor sensor simulation.
2.  A versioned sensor data contract shared by simulated and future
    physical devices.
3.  Validation, normalization and safe ingestion of readings.
4.  Raw sensor-reading persistence.
5.  Signal processing and rolling-window feature engineering.
6.  Statistical baseline analysis.
7.  Isolation Forest anomaly detection.
8.  Random Forest fault classification using labelled simulated data.
9.  Model training, serialization, versioning and loading.
10. Prediction evidence and confidence handling.
11. Model evaluation using held-out test data.
12. Automated tests, reproducibility checks and performance benchmarks.
13. Documentation and local commands to run the complete pipeline.

### 4.2 Explicitly out of scope

-   Physical ESP32, PLC or industrial sensor integration.
-   Frontend dashboards and chart components.
-   React Three Fiber / 3D motor implementation.
-   Cloud hosting, production deployment and paid infrastructure.
-   Automated repair execution or autonomous machine control.
-   Claims of certified industrial diagnosis or safety-critical
    prediction.
-   Deep learning unless separately approved in a later phase.
-   Microservices, Kubernetes, Redis or other infrastructure not
    justified by measured need.

## 5. Engineering principles

-   **Backend first:** implement reusable Python services before UI
    work.
-   **Local first:** all development and tests must run on a normal
    local machine.
-   **Zero budget:** use free and open-source libraries.
-   **Reproducibility:** fixed random seeds and recorded model/data
    versions.
-   **Separation of concerns:** simulation, validation, processing,
    models and persistence must be separate modules.
-   **Data integrity:** preserve raw readings; derived features must not
    overwrite source data.
-   **Safe predictions:** predictions are advisory and must include
    evidence and limitations.
-   **No leakage:** training and test data must be separated correctly.
-   **Backward-compatible contracts:** future hardware must be able to
    submit the same sensor payload format.
-   **Measured optimization:** do not add complexity before profiling
    demonstrates a need.

## 6. Sensor data requirements

### 6.1 Initial sensor channels

The first prototype uses:

  -----------------------------------------------------------------------
  Channel                 Unit                    Meaning
  ----------------------- ----------------------- -----------------------
  Temperature             °C                      Motor casing /
                                                  monitored motor
                                                  temperature

  Vibration               mm/s RMS                Overall vibration
                                                  velocity, represented
                                                  as an RMS value

  Timestamp               UTC ISO 8601            Time at which the
                                                  reading was observed

  Equipment ID            UUID or                 Motor that produced the
                          project-standard ID     reading

  Source                  string / enum           `simulator` initially;
                                                  future values may
                                                  include `esp32`

  Sequence number         integer                 Monotonically
                                                  increasing sequence
                                                  within a device stream
  -----------------------------------------------------------------------

Optional simulator metadata may include operating speed, load
percentage, scenario ID and simulation seed. These fields must be
clearly identified as simulated metadata, not assumed to be physical
sensor measurements.

### 6.2 Canonical payload

Use one canonical schema for simulator and future hardware ingestion.
Adapt field names to the existing Phase 2 contract if it already defines
one; do not create competing formats.

Example:

``` json
{
  "schema_version": "1.0",
  "equipment_id": "motor-001",
  "timestamp": "2026-01-15T10:30:00Z",
  "sequence": 1250,
  "source": "simulator",
  "measurements": {
    "temperature_c": 68.4,
    "vibration_mm_s_rms": 2.7
  },
  "operating_conditions": {
    "speed_rpm": 1480,
    "load_percent": 65.0
  },
  "simulation": {
    "scenario_id": "normal-run-01",
    "seed": 42
  }
}
```

The example values are illustrative, not diagnostic thresholds.

### 6.3 Validation rules

-   Require a valid equipment identifier, timestamp, sequence number and
    both required measurements.
-   Parse timestamps as timezone-aware values and normalize storage to
    UTC.
-   Reject NaN, positive/negative infinity, strings where numeric values
    are expected, and malformed timestamps.
-   Apply physically plausible configurable bounds to prevent corrupted
    input; keep these bounds in configuration, not scattered through
    code.
-   Reject negative vibration RMS values.
-   Do not silently clamp invalid readings into valid values.
-   Define duplicate handling using a stable idempotency key, such as
    equipment ID plus sequence number, or a unique event ID.
-   Handle out-of-order timestamps explicitly. Preserve valid
    late-arriving readings where policy permits; do not silently rewrite
    their timestamps.
-   Record validation failures in structured logs without exposing
    secrets.
-   Return clear validation errors through the API.

## 7. Deterministic sensor simulator

### 7.1 Purpose

The simulator supplies repeatable sensor streams and labelled scenarios
without requiring physical equipment. It must produce realistic-looking
variation while remaining transparent about being synthetic.

### 7.2 Required operating scenarios

  --------------------------------------------------------------------------------
  Scenario          Temperature       Vibration behaviour Label
                    behaviour                             
  ----------------- ----------------- ------------------- ------------------------
  Normal operation  Stable with small Low/stable with     `normal`
                    noise and gradual small noise         
                    drift                                 

  Excessive         Near normal or    Sustained elevated  `excessive_vibration`
  vibration         slightly elevated vibration           

  Overheating       Sustained         May remain near     `overheating`
                    temperature       normal              
                    increase                              

  Bearing-related   May rise          Characteristic      `bearing_abnormality`
  abnormality       gradually         elevated/variable   
                                      vibration           

  Combined          Elevated          Elevated vibration  `combined_abnormality`
  abnormality       temperature                           
  --------------------------------------------------------------------------------

These scenarios are synthetic patterns for software development. They
are not validated physical signatures of real motor faults.

### 7.3 Simulator features

The simulator must support:

-   Configurable sampling interval.
-   Configurable duration and number of samples.
-   Equipment ID selection.
-   Scenario selection and scenario duration.
-   Fixed random seed.
-   Normal noise and gradual drift.
-   Scenario transitions and optional recovery periods.
-   CSV export for offline training and evaluation.
-   Direct use by the ingestion service without bypassing validation.
-   A finite batch mode for tests and a continuous mode for local
    demonstrations.

### 7.4 Reproducibility

The same simulator configuration, scenario and seed must produce the
same sequence of readings. Store the seed and scenario metadata with
generated datasets. Avoid using the global random generator; use an
explicit seeded random generator.

## 8. Data ingestion and storage

### 8.1 Ingestion service

Create a dedicated service responsible for:

1.  Receiving a payload.
2.  Validating its schema and values.
3.  Checking equipment existence and active status.
4.  Applying duplicate/idempotency rules.
5.  Normalizing units and timestamps.
6.  Persisting the raw reading.
7.  Returning a stable response containing the stored reading ID and
    ingestion status.

The simulator must call the same service used by the API. Do not
implement a second ingestion path with different validation behaviour.

### 8.2 Raw data preservation

Raw readings are the source of truth. Never replace raw sensor values
with filtered or normalized feature values. Store derived features and
model outputs separately, linked to the source time window.

### 8.3 Suggested database entities

Align with the Phase 2 schema and migrations. The following are logical
requirements, not permission to duplicate existing tables.

**SensorReadings** - `id` - `equipment_id` - `timestamp` - `sequence` -
`source` - `temperature_c` - `vibration_mm_s_rms` - optional
operating-condition fields - `schema_version` - `created_at`

**FeatureWindows** - `id` - `equipment_id` - `window_start` -
`window_end` - `sample_count` - feature values -
`feature_schema_version` - `created_at`

**AnomalyEvents** - `id` - `equipment_id` - `detected_at` -
`window_start` - `window_end` - `anomaly_score` - `severity` -
`detector_name` - `model_version` - `evidence_json`

**MLPredictions** - `id` - `equipment_id` - `predicted_at` -
`window_start` - `window_end` - `predicted_fault` - `confidence` -
`model_name` - `model_version` - `feature_schema_version` -
`evidence_json`

**ModelRegistry** - `id` - `model_name` - `model_version` -
`algorithm` - `artifact_path` - `feature_schema_version` -
`training_dataset_version` - `metrics_json` - `created_at` - `is_active`

Use the Phase 2 migration system (Alembic) for schema changes. Avoid
storing large model binaries inside SQLite; store artifacts as local
files and keep metadata/path/checksum in the database. Ensure paths are
controlled by the application and never accept arbitrary artifact paths
from API clients.

### 8.4 Indexing and retention

At minimum, evaluate indexes for: - `(equipment_id, timestamp)` -
`(equipment_id, sequence)` or the chosen idempotency key -
`(equipment_id, detected_at)` for anomaly events -
`(equipment_id, predicted_at)` for predictions

Use pagination for reading histories. Define configurable retention for
raw data and derived data, but do not delete records automatically in
the initial prototype unless an explicit retention job and tests exist.
Document SQLite write-concurrency limitations and use short
transactions.

## 9. Signal processing

### 9.1 Goals

Signal processing prepares sensor readings for analysis. It must be
deterministic, tested and separated from persistence and model code.

### 9.2 Required processing steps

1.  Sort readings by timestamp and sequence according to the documented
    ordering policy.
2.  Detect missing samples and irregular sampling intervals.
3.  Identify invalid values; do not fabricate replacement values
    silently.
4.  Apply optional smoothing for analysis while retaining raw values.
5.  Segment readings into configurable rolling or fixed windows.
6.  Calculate feature values for each valid window.
7.  Mark windows with insufficient data as incomplete rather than
    generating misleading features.

### 9.3 Initial window configuration

Use a configurable window size and stride. A sensible starting
experiment is a 10-second window with a 5-second stride, assuming a 1 Hz
simulated sampling rate. These are development defaults only and must be
configurable. Document the relationship between sample rate, window
duration and stride.

### 9.4 Initial feature set

For temperature and vibration independently where applicable:

-   Mean
-   Median
-   Minimum and maximum
-   Standard deviation
-   Root mean square (RMS)
-   Peak-to-peak range
-   First-to-last change / slope estimate
-   Rate of change
-   Rolling variability

For vibration, consider crest factor only if the underlying signal
representation supports it. A single RMS vibration channel cannot
support meaningful frequency-spectrum analysis or waveform-derived
features. Do not pretend that FFT, spectral peaks or bearing defect
frequencies can be inferred from RMS-only readings.

If future hardware supplies raw acceleration waveforms, define a
separate waveform data contract and a later signal-processing extension
for FFT and frequency-domain features.

### 9.5 Feature schema

-   Give the feature set a version identifier.
-   Keep feature names and units stable within a version.
-   Store the version with every feature window and model.
-   Validate feature order and presence before inference.
-   Do not silently substitute missing features with zero.
-   Keep feature extraction reusable for training and inference so both
    paths calculate identical features.

## 10. Statistical baseline

Before machine learning, implement a transparent statistical baseline.

Requirements: - Calculate baseline mean and standard deviation from a
designated normal training period. - Support configurable limits or
z-score-based deviation checks. - Avoid fitting baselines using
evaluation/test data. - Persist or version baseline parameters. - Return
the measured value, baseline value, deviation and rule that triggered
the alert. - Make thresholds configurable and document that initial
values are experimental.

The statistical baseline provides an understandable comparison for
Isolation Forest and helps identify obvious simulator or data-quality
defects.

## 11. Anomaly detection --- Isolation Forest

### 11.1 Purpose

Use Scikit-learn Isolation Forest to identify unusual feature windows.
This is an anomaly detector, not a definitive fault classifier.

### 11.2 Inputs

Use a documented subset of numeric window features, such as: - Mean
temperature. - Temperature standard deviation and slope. - Mean
vibration RMS. - Vibration standard deviation and maximum. - Relevant
operating-condition features when consistently available.

### 11.3 Training requirements

-   Train primarily on normal-operation windows for the initial
    anomaly-detection experiment.
-   Split data by scenario run or time block where possible, not by
    randomly splitting highly overlapping windows.
-   Fit preprocessing only on training data.
-   Fix random state.
-   Record contamination or threshold-selection policy.
-   Save the model artifact and metadata.
-   Evaluate on separate normal and abnormal runs.

### 11.4 Output contract

An anomaly result should include: - `is_anomaly` - raw anomaly score /
decision score - configured threshold or decision rule - detector name
and model version - feature-window ID and time range - concise evidence
fields identifying unusual feature values

Do not present the score as a probability unless it has been calibrated
and validated as one.

## 12. Fault classification --- Random Forest

### 12.1 Purpose

Use a supervised Random Forest classifier to predict one of the known
synthetic operating-condition labels.

### 12.2 Initial classes

-   `normal`
-   `excessive_vibration`
-   `overheating`
-   `bearing_abnormality`
-   `combined_abnormality`

Keep labels in one shared enum/constant definition to prevent spelling
drift across simulator, training, API and tests.

### 12.3 Dataset requirements

-   Generate labelled samples from multiple independent simulation runs.
-   Use different seeds and parameter combinations to create variation.
-   Ensure every class has adequate representation.
-   Keep scenario/run identifiers so data splitting can prevent leakage.
-   Separate train, validation and test data by run or time block.
-   Do not randomly split adjacent overlapping windows into both train
    and test.
-   Keep the test set untouched until final evaluation.
-   Store dataset generation configuration and version.

### 12.4 Training and inference

-   Use a reproducible pipeline with preprocessing and classifier where
    needed.
-   Fix random state.
-   Evaluate class imbalance and use appropriate class weighting if
    justified.
-   Persist class labels and feature schema alongside the artifact.
-   Validate feature names/order at inference time.
-   Return predicted class and per-class scores where supported.
-   Treat classifier scores as model confidence estimates, not
    guaranteed probabilities or certainty.
-   Support an `unknown` / `insufficient_data` outcome when inputs are
    invalid, incomplete or outside supported conditions.

### 12.5 Combining anomaly detection and classification

Keep anomaly detection and classification as separate outputs: -
Isolation Forest answers: "Does this feature window look unusual
relative to the learned normal baseline?" - Random Forest answers:
"Which known simulated class most resembles this feature window?"

Do not force the classifier to label every anomaly as a known fault. If
the anomaly detector flags an unusual window but classifier evidence is
weak or inconsistent, return an uncertain/unknown advisory state.

## 13. Prediction evidence and explainability

Every stored prediction should be traceable to: - Equipment ID. - Source
sensor-reading IDs or feature-window ID. - Window start/end
timestamps. - Feature schema version. - Model name and model version. -
Predicted label and score. - Anomaly result and score, when available. -
Key feature values that support the result. - Training dataset version
and evaluation metrics reference.

Provide human-readable evidence such as: - "Vibration mean is higher
than the normal baseline." - "Temperature increased across the selected
window." - "The window contains fewer samples than required."

Evidence must be derived from actual computed features and configured
baselines. Do not invent mechanical root causes. Component mapping (for
example, bearing area highlighting) is a later integration and must be
described as a possible association, not proof that a component has
failed.

## 14. Model lifecycle and artifact management

Create a simple local model lifecycle:

1.  Generate a versioned dataset.
2.  Validate labels and feature schema.
3.  Split data without leakage.
4.  Train model.
5.  Evaluate on held-out data.
6.  Save artifact and metadata.
7.  Register the model version.
8.  Load the explicitly active version for inference.
9.  Record the model version on every prediction.

Requirements: - Use safe, controlled artifact directories. - Save
checksums for artifacts. - Do not load arbitrary files or user-supplied
serialized models. - Treat pickle/joblib artifacts as trusted
application-generated files only. - Fail safely if an artifact is
missing, corrupted or incompatible. - Keep the previous valid model
available when a new model fails validation. - Make model activation
explicit; training must not silently replace the active model.

## 15. Evaluation and acceptance metrics

### 15.1 Classification metrics

Report: - Accuracy. - Precision, recall and F1-score (macro and per
class). - Confusion matrix. - Per-class support. - Training and
inference duration.

Macro averages are important because overall accuracy can hide poor
performance on a minority fault class.

### 15.2 Anomaly metrics

Where ground-truth scenario labels exist, report: - Precision. -
Recall. - F1-score. - False-positive rate on normal windows. - Detection
rate on abnormal windows. - Detection delay where the simulation
timeline permits it.

### 15.3 Evaluation rules

-   Evaluate only on held-out data.
-   Do not tune thresholds on the final test set.
-   Record dataset version, random seed, model version and
    configuration.
-   Compare ML results with the statistical baseline.
-   Include limitations and failure cases in the report.
-   Do not claim industrial accuracy from synthetic data.

### 15.4 Initial acceptance targets

Targets are development gates, not claims about real equipment: - Every
class is represented in train and test partitions. - No train/test
overlap of source simulation runs. - No missing or non-finite model
input reaches inference. - The pipeline can process a complete
deterministic test dataset end to end. - Metrics and confusion matrix
are generated reproducibly. - A failed or uncertain inference is
represented explicitly rather than silently converted to `normal`. -
Performance is measured and documented on the developer's machine.

Do not impose an arbitrary high accuracy target that encourages leakage
or overfitting. First establish a trustworthy evaluation protocol, then
set model-quality targets based on results.

## 16. Backend API requirements

Follow the Phase 2 API naming, authentication and response conventions.
These are proposed endpoint capabilities; adapt prefixes and names to
the existing API rather than creating duplicate routes.

  ----------------------------------------------------------------------------------------------------
  Method                  Endpoint                                             Purpose
  ----------------------- ---------------------------------------------------- -----------------------
  POST                    `/api/v1/sensor-readings`                            Ingest one validated
                                                                               reading

  POST                    `/api/v1/sensor-readings/batch`                      Ingest a bounded batch

  GET                     `/api/v1/equipment/{equipment_id}/sensor-readings`   Paginated reading
                                                                               history

  POST                    `/api/v1/simulator/start`                            Start a local
                                                                               simulation job if job
                                                                               control is implemented

  POST                    `/api/v1/simulator/stop`                             Stop a simulation job

  GET                     `/api/v1/simulator/status`                           Read simulator status

  POST                    `/api/v1/ml/train`                                   Trigger a protected
                                                                               local training job

  GET                     `/api/v1/ml/models`                                  List registered model
                                                                               versions

  POST                    `/api/v1/ml/models/{model_id}/activate`              Explicitly activate a
                                                                               validated model

  POST                    `/api/v1/ml/predict`                                 Run inference on a
                                                                               valid feature window

  GET                     `/api/v1/equipment/{equipment_id}/predictions`       Paginated prediction
                                                                               history

  GET                     `/api/v1/equipment/{equipment_id}/anomalies`         Paginated anomaly
                                                                               history

  GET                     `/api/v1/ml/evaluation/{run_id}`                     Retrieve evaluation
                                                                               results
  ----------------------------------------------------------------------------------------------------

API requirements: - Require authentication and role authorization
according to Phase 2. - Training and model activation must be restricted
to administrator roles. - Operators may read permitted monitoring
outputs but must not trigger training or activate models. - Technicians
may inspect predictions and create maintenance records according to the
role matrix. - Enforce request-size and batch-size limits. - Use
consistent error response structures. - Validate equipment
ownership/access before returning records. - Add pagination and bounded
time-range filters. - Do not expose local filesystem paths, stack
traces, secrets or internal model artifacts. - Long-running training
must not block the API request loop. For the local prototype, use a
controlled background job mechanism; avoid adding a broker unless
required.

## 17. Performance and reliability

Measure before optimizing. Record: - Readings ingested per second in
batch mode. - Single-reading and batch-ingestion latency. - Feature
extraction time per window. - Anomaly detection and classification
latency. - Database query latency for paginated histories. - Memory use
during dataset generation and training. - Behaviour under sustained
simulator load.

Engineering requirements: - Use bounded batches and avoid loading
unlimited histories into memory. - Use vectorized NumPy/Pandas
operations where they improve measured performance. - Keep database
transactions short. - Avoid one database write per tiny intermediate
feature operation where batching is practical. - Avoid running model
training inside a synchronous request handler. - Apply timeouts and
controlled cancellation to simulation/training jobs. - Ensure a
simulator can be stopped cleanly. - Handle database lock/busy errors
with bounded retry where appropriate; do not retry indefinitely. -
Ensure repeated ingestion of the same idempotency key does not create
duplicate readings.

## 18. Security requirements

-   Reuse Phase 2 authentication and authorization; do not create a
    second login system.
-   Restrict simulator controls, training and model activation by role.
-   Validate every API payload and query parameter.
-   Apply maximum batch sizes and request limits.
-   Prevent path traversal in model artifact handling.
-   Never accept executable model artifacts from ordinary API clients.
-   Do not expose credentials, tokens, personal data or sensitive
    payloads in logs.
-   Keep secrets in environment variables or local configuration
    excluded from version control.
-   Use parameterized ORM queries; never build SQL from untrusted
    strings.
-   Avoid unrestricted file uploads.
-   Return generic internal errors to clients while preserving safe
    diagnostic logs.
-   Add tests for unauthorized access, invalid payloads, oversized
    batches and path manipulation.

## 19. Suggested code organization

Adapt to the repository structure established in Phase 2. One possible
organization is:

``` text
backend/
  app/
    api/
      v1/
        sensor_readings.py
        simulator.py
        ml.py
    core/
      config.py
      logging.py
      security.py
    db/
      session.py
      models/
        sensor_reading.py
        feature_window.py
        anomaly_event.py
        ml_prediction.py
        model_registry.py
    schemas/
      sensor.py
      features.py
      predictions.py
      simulator.py
    services/
      ingestion_service.py
      simulator_service.py
      signal_processing_service.py
      feature_engineering_service.py
      anomaly_service.py
      classification_service.py
      prediction_service.py
      model_registry_service.py
    ml/
      datasets/
      training/
      evaluation/
      artifacts/
      pipelines/
    tests/
      unit/
      integration/
      api/
      performance/
    scripts/
      generate_dataset.py
      train_models.py
      evaluate_models.py
      run_simulator.py
```

Keep generated datasets, model artifacts, logs and local databases
outside source-controlled code where appropriate. Add safe `.gitignore`
rules. Do not commit secrets or large generated artifacts unless the
repository's policy explicitly requires it.

## 20. Testing strategy

### 20.1 Unit tests

-   Sensor schema validation.
-   Timestamp normalization.
-   Duplicate and out-of-order reading handling.
-   Simulator determinism with fixed seed.
-   Scenario label correctness.
-   Feature calculations against known small arrays.
-   Insufficient-window handling.
-   Baseline calculations.
-   Model input schema validation.
-   Model artifact metadata and checksum checks.

### 20.2 Integration tests

-   Simulator → ingestion → SQLite.
-   Stored readings → feature extraction.
-   Feature windows → anomaly detector.
-   Feature windows → classifier.
-   Prediction → database persistence.
-   Model registration → activation → inference.
-   API authentication and role permissions.
-   Batch ingestion with duplicate entries.

### 20.3 Regression tests

-   Same seed and configuration produce the same dataset.
-   Feature schema changes require an explicit version change.
-   Existing Phase 2 authentication and equipment APIs continue to work.
-   API response shapes remain consistent.
-   Previously stored raw readings remain unchanged after processing.

### 20.4 Performance tests

Use repeatable local test sizes (for example 10,000 and 100,000 readings
where the machine permits). Record machine specifications, dataset size,
configuration and elapsed time. Do not make unsupported universal
performance claims.

## 21. Milestone-by-milestone implementation plan

Complete and verify each milestone before moving on.

### Milestone 0 --- Repository and Phase 2 audit

-   Read Phase 1 and Phase 2 documents completely.
-   Inspect the repository and current branch.
-   Identify existing API, database, auth, equipment and migration
    implementations.
-   Identify existing conventions and tests.
-   Produce a short gap analysis.
-   Do not overwrite working Phase 2 modules or create duplicate
    models/routes.
-   Record any conflict between this specification and the existing
    Phase 2 baseline; prefer the established Phase 2 contract unless the
    user approves a change.

**Exit criteria:** architecture and implementation gaps are documented;
implementation plan matches the real repository.

### Milestone 1 --- Sensor contract and simulator

-   Define versioned Pydantic schemas.
-   Implement deterministic scenario generation.
-   Implement finite batch and continuous modes.
-   Add seed, scenario and equipment configuration.
-   Export labelled datasets to CSV.
-   Add simulator unit tests.

**Exit criteria:** all five scenarios generate valid, repeatable
readings using the canonical contract.

### Milestone 2 --- Ingestion, validation and raw storage

-   Implement shared ingestion service.
-   Add duplicate/idempotency handling.
-   Normalize timestamps and validate numeric values.
-   Add/adjust SQLAlchemy models and Alembic migrations.
-   Add indexes and bounded batch ingestion.
-   Add API endpoints and authorization.

**Exit criteria:** simulator and API use the same ingestion path;
readings persist correctly and duplicate submissions are safe.

### Milestone 3 --- Signal processing and feature engineering

-   Implement window segmentation.
-   Handle gaps, irregular intervals and insufficient data.
-   Calculate the initial feature set.
-   Version feature schemas.
-   Store feature windows where persistence is required.
-   Add deterministic unit and integration tests.

**Exit criteria:** a known reading sequence produces expected, versioned
features without modifying raw readings.

### Milestone 4 --- Statistical baseline

-   Generate normal baseline data.
-   Fit and version baseline parameters.
-   Implement transparent deviation rules.
-   Persist anomaly evidence.
-   Compare baseline behaviour across scenarios.

**Exit criteria:** baseline results are reproducible and explainable.

### Milestone 5 --- Isolation Forest

-   Build a training dataset from normal windows and separate abnormal
    evaluation runs.
-   Train the detector with a fixed seed.
-   Save artifact and metadata.
-   Implement inference service.
-   Evaluate false positives and abnormal detection.
-   Persist anomaly events and evidence.

**Exit criteria:** detector runs end to end on held-out simulated
scenarios and reports metrics.

### Milestone 6 --- Random Forest classification

-   Generate a balanced, versioned labelled dataset.
-   Split by independent run/scenario to prevent leakage.
-   Train the classifier pipeline.
-   Evaluate per-class metrics and confusion matrix.
-   Save and register the model.
-   Implement prediction service and uncertain outcome handling.

**Exit criteria:** all five classes are represented and evaluation is
performed on independent held-out runs.

### Milestone 7 --- Unified prediction pipeline

-   Connect feature extraction, baseline, anomaly detector and
    classifier.
-   Keep anomaly and classification results separate.
-   Add evidence generation.
-   Persist predictions with model and feature versions.
-   Add paginated history endpoints.

**Exit criteria:** one valid sensor stream can produce stored, traceable
advisory results end to end.

### Milestone 8 --- Hardening and performance

-   Add failure handling and bounded retries.
-   Test simulator stop/cancellation.
-   Test large batches and long histories.
-   Profile CPU, memory and database performance.
-   Fix measured bottlenecks.
-   Run security and regression tests.

**Exit criteria:** no critical test failures; limitations and benchmark
results are documented.

### Milestone 9 --- Documentation and Phase 3 sign-off

-   Document setup and commands.
-   Document schemas, APIs, feature definitions and model lifecycle.
-   Include example generated dataset and evaluation report where
    practical.
-   Document synthetic-data limitations.
-   Verify all acceptance criteria.
-   Produce a Phase 3 completion report and list of Phase 4
    prerequisites.

**Exit criteria:** another developer can run the complete local pipeline
using the documentation.

## 22. Local development commands

The coding assistant must adapt exact commands to the existing package
manager and project layout. A typical workflow may provide commands
equivalent to:

``` bash
# Install backend dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Generate a deterministic labelled dataset
python -m app.scripts.generate_dataset --seed 42 --output data/generated/

# Train models
python -m app.scripts.train_models

# Evaluate models
python -m app.scripts.evaluate_models

# Run the API
uvicorn app.main:app --reload

# Run tests
pytest -q
```

Do not add commands that do not exist. Update the README with the actual
verified commands after implementation.

## 23. Dependencies

Use the versions already selected in the repository where possible. The
intended free stack includes:

-   Python
-   FastAPI and Pydantic
-   SQLAlchemy 2
-   Alembic
-   SQLite
-   NumPy
-   Pandas
-   SciPy where needed
-   Scikit-learn
-   Joblib for trusted local model artifacts
-   Pytest
-   HTTPX for API tests

Avoid adding dependencies without a clear need. Pin or constrain
versions in the project's existing dependency-management format and
verify compatibility.

## 24. Risks and mitigations

  -----------------------------------------------------------------------
  Risk                                Mitigation
  ----------------------------------- -----------------------------------
  Synthetic data makes models appear  Split by independent simulation
  unrealistically accurate            runs; document synthetic-only
                                      validation

  Overlapping windows cause data      Partition by run/time block before
  leakage                             window generation or preserve run
                                      IDs through splitting

  RMS-only vibration is mistaken for  Explicitly limit features; defer
  waveform data                       FFT until waveform samples exist

  Classifier always forces a known    Add insufficient-data and uncertain
  label                               outcomes; keep anomaly detection
                                      separate

  Model artifact becomes incompatible Store model and feature schema
                                      versions; validate before
                                      activation

  SQLite write contention             Use short transactions, bounded
                                      batches and measured concurrency

  Simulator bypasses API validation   Route simulator output through the
                                      shared ingestion service

  Excessive data growth               Define retention policy, pagination
                                      and benchmark storage growth

  Untraceable predictions             Persist source window, model
                                      version, feature version and
                                      evidence

  False confidence in diagnosis       Label outputs advisory and
                                      synthetic-data-based
  -----------------------------------------------------------------------

## 25. Phase 3 acceptance checklist

Phase 3 is complete only when the following can be demonstrated locally:

-   [ ] Existing Phase 1 and Phase 2 requirements have been reviewed.
-   [ ] One canonical, versioned sensor data contract is used.
-   [ ] Simulator produces all five labelled scenarios.
-   [ ] Fixed seeds reproduce identical datasets.
-   [ ] Simulator supports batch generation and controlled continuous
    operation.
-   [ ] Ingestion validates payloads and timestamps.
-   [ ] Duplicate readings are handled idempotently.
-   [ ] Raw readings persist in SQLite and are not overwritten by
    processing.
-   [ ] Database migrations and indexes are tested.
-   [ ] Feature windows are deterministic and versioned.
-   [ ] Missing/insufficient data is handled explicitly.
-   [ ] Statistical baseline produces traceable evidence.
-   [ ] Isolation Forest trains, saves, loads and evaluates
    successfully.
-   [ ] Random Forest trains, saves, loads and evaluates successfully.
-   [ ] Dataset splitting prevents run/window leakage.
-   [ ] Precision, recall, F1-score, confusion matrix and false-positive
    rate are reported as applicable.
-   [ ] Predictions include source window, model version and feature
    schema version.
-   [ ] API endpoints enforce authentication and role permissions.
-   [ ] Batch sizes, query ranges and memory use are bounded.
-   [ ] Unit, integration, API, regression and performance tests pass.
-   [ ] Local setup and execution instructions are verified.
-   [ ] Synthetic-data limitations are clearly documented.

## 26. Instructions for the OpenAI + OmniRoute coding assistant

The following instructions are mandatory when implementing this
document.

1.  Read this entire Phase 3 document, the Phase 1 requirements document
    and the Phase 2 backend architecture document before editing code.
2.  Inspect the existing repository, current code, dependencies,
    database schema, migrations, API routes, authentication and tests.
3.  Treat Phase 1 and Phase 2 as the established project baseline. Do
    not casually rename, replace or duplicate existing modules.
4.  Keep backend, APIs, database, storage, performance, security and
    authentication as the priority.
5.  Do not start frontend, 3D visualization, deployment or cloud work in
    this phase.
6.  Do not introduce paid APIs, paid services, paid hosting or hardware
    dependencies.
7.  Do not introduce microservices, Redis, Kubernetes or a message
    broker without demonstrating a requirement and obtaining approval.
8.  Implement only one milestone at a time. Before coding a milestone,
    state its scope and the files expected to change.
9.  After each milestone, run relevant tests, inspect failures, fix
    regressions and report the exact commands and results.
10. Do not claim a test passed unless it was actually run and passed.
11. Do not delete existing code or migrations to make tests pass.
    Explain and resolve conflicts safely.
12. Use type hints, clear naming, small service modules, Pydantic
    validation and SQLAlchemy best practices.
13. Keep secrets out of source control and logs.
14. Preserve raw sensor data and maintain traceability for every derived
    feature and prediction.
15. Do not use synthetic model accuracy as evidence of real industrial
    performance.
16. If a requirement is ambiguous or conflicts with Phase 2, explain the
    issue and propose the smallest safe resolution instead of silently
    changing the architecture.
17. Keep documentation and example commands synchronized with the actual
    implementation.
18. Do not proceed to the next milestone until the current milestone's
    exit criteria are met or the user explicitly approves proceeding
    with known gaps.

### First task for the coding assistant

Start with **Milestone 0 --- Repository and Phase 2 audit**.

Do not immediately implement the entire Phase 3. First: - Locate and
read the Phase 1 and Phase 2 documents. - Inspect the backend
repository. - Summarize the current architecture and existing reusable
modules. - Identify missing components and conflicts. - Propose the
exact Milestone 1 file changes and tests.

Wait for approval before making implementation changes if the repository
state or project conventions are unclear.

------------------------------------------------------------------------

## 27. Phase 3 deliverables

At the end of this phase, the project should contain:

1.  A deterministic electric-motor sensor simulator.
2.  A shared sensor data contract and validation layer.
3.  A tested ingestion service and persisted raw sensor readings.
4.  A versioned signal-processing and feature-engineering pipeline.
5.  A statistical baseline detector.
6.  A trained and evaluated Isolation Forest model.
7.  A trained and evaluated Random Forest classifier.
8.  A local model registry and safe artifact lifecycle.
9.  Persisted anomaly events, predictions and evidence.
10. Protected API endpoints for ingestion, simulation status, model
    operations and prediction history.
11. Automated test coverage and reproducible benchmark/evaluation
    reports.
12. Updated developer documentation.

**Phase 3 outcome:** MechTech can generate motor sensor data, ingest and
store it safely, derive features, detect unusual patterns, classify
known simulated conditions and persist traceable advisory results ---
entirely on a local development machine.

**Important limitation:** successful Phase 3 completion validates the
software pipeline against synthetic scenarios only. Real-world fault
diagnosis requires suitable physical sensor data, domain validation and
testing on actual equipment in a later phase.
