# MechTech — Database Design

**Version:** 1.0 · **Database:** PostgreSQL · **ORM:** SQLAlchemy · **Migrations:** Alembic

## 1. Goals and conventions
- UUID primary keys for externally addressable records.
- `TIMESTAMPTZ` for timestamps; store UTC.
- Explicit units for all telemetry.
- Foreign keys, unique constraints, check constraints, and transactions.
- `created_at` and `updated_at` on mutable entities.
- JSONB only for genuinely variable, versioned attributes—not as a substitute for relational modeling.
- Archive business records when history depends on them; define retention before real data is collected.
- Use migrations for every schema change; never rely on automatic production table creation.

## 2. Identity and access

### `users`
`id UUID PK`, `email CITEXT UNIQUE NOT NULL`, `password_hash TEXT NULL`, `display_name TEXT NOT NULL`, `status TEXT NOT NULL`, `email_verified_at`, `last_login_at`, `created_at`, `updated_at`.

Statuses: `pending`, `active`, `rejected`, `suspended`. A password hash may be null for a future external identity provider, but external login is not required initially.

### `registration_requests`
`id UUID PK`, `user_id UUID FK users UNIQUE`, `status`, `reviewed_by UUID FK users NULL`, `reviewed_at`, `review_note`, `created_at`.

Pending accounts cannot establish protected sessions. Record approval/rejection and the reviewing administrator.

### `roles` and `permissions`
Roles: `id`, unique `key`, `name`, `scope` (`platform` or `organization`), description. Permissions: `id`, unique `key`, description.

### `role_permissions`
`role_id FK`, `permission_id FK`, composite primary key.

### `user_roles`
`user_id FK`, `role_id FK`, `organization_id FK NULL`; unique role assignment. Platform roles have no organization; organization roles require one. Enforce this rule in application validation and database constraints where practical.

### `sessions`
`id UUID PK`, `user_id FK`, `token_hash UNIQUE`, `created_at`, `expires_at`, `last_seen_at`, `revoked_at`.

Store only a hash of the opaque session token. Index `user_id`, `expires_at`, and active-session lookups.

## 3. Organizations

### `organizations`
`id UUID PK`, `name`, unique `slug`, `status`, `created_at`, `updated_at`.

### `organization_members`
`id UUID PK`, `organization_id FK`, `user_id FK`, `membership_status`, `joined_at`; unique `(organization_id, user_id)`.

Tenant-owned records must have a clear organization ownership path. Major tenant-owned tables should include `organization_id` where it improves safe scoping and query performance. Validate parent/child organization consistency. Consider PostgreSQL row-level security only after its operational and migration implications are understood; application-level tenant scoping remains mandatory.

## 4. Equipment

### `equipment_types`
`id UUID PK`, unique `key` (initially `electric_motor`), `name`, `schema_version`, `is_enabled`.

### `equipment`
`id UUID PK`, `organization_id FK`, `equipment_type_id FK`, `asset_tag`, `name`, `manufacturer`, `model_number`, `serial_number`, `installation_date`, `status`, `location_label`, `created_by FK users`, timestamps.

Unique `(organization_id, asset_tag)` when asset tag is non-null. Index `(organization_id, status)` and `(organization_id, equipment_type_id)`.

### `equipment_specifications`
`id UUID PK`, `equipment_id FK UNIQUE`, `schema_version`, `specification JSONB`.

Motor-specific fields can include rated power, voltage, current, speed, phase, frequency, and motor type. Validate JSON against a versioned schema at the application boundary.

### `components`
`id UUID PK`, `organization_id FK`, `equipment_id FK`, `parent_component_id FK components NULL`, `component_type`, `name`, manufacturer/model, status, timestamps.

Parent and child must belong to the same equipment and organization. Index `(equipment_id, parent_component_id)`.

### `equipment_assignments`
`id UUID PK`, `equipment_id FK`, `user_id FK`, `assignment_type`, `assigned_by FK users`, `assigned_at`, `ended_at`.

Use assignment history rather than overwriting who previously owned responsibility.

## 5. Sensors and telemetry

### `sensors`
`id UUID PK`, `organization_id FK`, `equipment_id FK`, `component_id FK NULL`, `sensor_key`, `measurement_type`, `unit`, `status`, `configuration JSONB`, timestamps.

Unique `(equipment_id, sensor_key)`. Validate that an optional component belongs to the same equipment.

### `sensor_readings`
`id UUID PK`, `organization_id FK`, `sensor_id FK`, `value DOUBLE PRECISION`, `unit`, `recorded_at TIMESTAMPTZ`, `received_at TIMESTAMPTZ`, `source`, `idempotency_key NULL`, `quality_status`, optional metadata JSONB.

Initial indexes:
- `(sensor_id, recorded_at DESC)`
- `(organization_id, recorded_at DESC)`
- Unique `(sensor_id, idempotency_key)` when the key is present.

Store source event time separately from server receipt time. Define accepted clock skew and retention policy. Consider time partitioning only after measuring volume; partitioning changes unique-key design and migration complexity.

### `monitoring_rules`
`id UUID PK`, `organization_id FK`, optional `equipment_type_id FK`, `name`, `measurement_type`, `operator`, `threshold NUMERIC`, `unit`, `duration_seconds`, `severity`, `is_enabled`, `version`, `created_by`, timestamps.

Represent supported operators as a controlled enum or validated key. Do not evaluate arbitrary user-provided expressions.

### `anomalies`
`id UUID PK`, `organization_id FK`, `equipment_id FK`, optional sensor/rule references, `detected_at`, `severity`, `summary`, `evidence JSONB`, `status`.

### `alerts`
`id UUID PK`, `organization_id FK`, `equipment_id FK`, optional `anomaly_id FK`, title/description, severity, status (`open`, `acknowledged`, `resolved`, `dismissed`), created/acknowledged/resolved timestamps, actor references, resolution note.

Index `(organization_id, status, created_at DESC)` and `(equipment_id, created_at DESC)`.

## 6. ML and diagnostics

### `ml_models`
`id UUID PK`, `model_key`, `version`, `equipment_type_id FK`, optional artifact file FK, `feature_schema JSONB`, dataset version, `metrics JSONB`, status (`draft`, `validated`, `active`, `retired`), created_at.

Unique `(model_key, version)`. Only validated and explicitly activated versions may be used for normal inference.

### `predictions`
`id UUID PK`, `organization_id FK`, `equipment_id FK`, `model_id FK`, `predicted_at`, `output JSONB`, optional confidence, input window start/end, optional feature snapshot, status.

Persist the model version and feature window so results can be audited and reproduced where possible.

### `faults`
`id UUID PK`, unique `key`, `name`, `description`, `equipment_type_id FK`, optional default severity.

### `diagnoses`
`id UUID PK`, `organization_id FK`, `equipment_id FK`, status, optional primary fault FK, severity, evidence strength, summary, `diagnostic_policy_version`, `generated_at`, optional reviewer FK/time/note.

Recommended statuses: `possible_fault`, `insufficient_data`, `under_review`, `confirmed_by_reviewer`, `dismissed`.

### `diagnosis_evidence`
`id UUID PK`, `diagnosis_id FK`, `evidence_type` (`rule`, `prediction`, `graph`, `sensor`, `manual`), optional source reference, `details JSONB`, `created_at`.

Keep compact evidence snapshots and source identifiers. Do not rely only on a mutable upstream record to explain a historical diagnosis.

## 7. Knowledge graph

### `knowledge_nodes`
`id UUID PK`, `node_type`, `key`, `label`, `description`, optional `equipment_type_id FK`, `attributes JSONB`, `version`, timestamps.

Examples: component, symptom, fault, cause, inspection, repair, operating_condition.

### `knowledge_edges`
`id UUID PK`, `source_node_id FK`, `target_node_id FK`, `relationship_type`, `weight`, `confidence`, `description`, `attributes JSONB`, `version`, timestamps.

Index source and target node IDs. Validate allowed relationship types. Avoid storing duplicate edges with the same source, target, type, and version unless parallel edges are intentional.

## 8. Maintenance, files, audit, and jobs

### `maintenance_records`
`id UUID PK`, `organization_id FK`, `equipment_id FK`, optional `diagnosis_id FK`, optional `alert_id FK`, `created_by FK`, `assigned_to FK NULL`, `title`, `description`, `maintenance_type`, `status`, `priority`, `scheduled_at`, `started_at`, `completed_at`, `outcome`, timestamps.

### `stored_files`
`id UUID PK`, `organization_id FK`, `uploaded_by FK`, `storage_key UNIQUE`, `original_filename`, `media_type`, `size_bytes`, `checksum`, `purpose`, `created_at`.

Never use the original filename as a storage path. Authorize every file read.

### `audit_logs`
`id UUID PK`, optional `organization_id`, `actor_user_id`, `action`, `resource_type`, `resource_id`, `request_id`, `created_at`, `details JSONB`.

Append audit events; restrict update/delete permissions. Avoid logging passwords, tokens, secrets, or unnecessary personal data.

### `background_jobs`
`id UUID PK`, `job_type`, `payload JSONB`, `status`, `attempt_count`, `max_attempts`, `available_at`, `locked_at`, `locked_by`, `last_error`, `created_at`, `completed_at`.

Index `(status, available_at)`. Claim jobs transactionally; handlers should be idempotent. Sanitize error messages before storing or displaying them.

## 9. Relationship overview

```text
users --< organization_members >-- organizations
users --< sessions
users --< user_roles >-- roles --< role_permissions >-- permissions
organizations --< equipment --< components
equipment --< sensors --< sensor_readings
equipment --< monitoring_rules
equipment --< anomalies --< alerts
equipment --< predictions >-- ml_models
equipment --< diagnoses --< diagnosis_evidence
diagnoses --> faults
knowledge_nodes --< knowledge_edges >-- knowledge_nodes
equipment --< maintenance_records
organizations --< stored_files
users --< audit_logs
```

## 10. Integrity and transaction rules
- Create registration request and pending user in one transaction.
- Approve a registration and activate membership/role assignment atomically.
- Create equipment and its specifications in one transaction.
- Verify organization ownership for every referenced sensor, equipment, component, diagnosis, and file.
- Persist readings before enqueueing processing; use an outbox or transactionally inserted job to avoid lost work.
- Create alert and anomaly state changes atomically.
- Store diagnosis and its evidence in one transaction.
- Use optimistic concurrency (`version` column) for records that can be edited by multiple administrators.
- Prefer soft archival for equipment and reference data; never silently rewrite historical telemetry or diagnosis evidence.

## 11. Indexing strategy
Start with indexes that match actual API access paths:
- Users: unique normalized email.
- Memberships: unique `(organization_id, user_id)`.
- Equipment: `(organization_id, status)`, unique tenant asset tag.
- Sensors: unique `(equipment_id, sensor_key)`.
- Readings: `(sensor_id, recorded_at DESC)`.
- Alerts: `(organization_id, status, created_at DESC)`.
- Diagnoses: `(organization_id, status, generated_at DESC)`.
- Graph edges: `(source_node_id, relationship_type)` and `(target_node_id, relationship_type)`.
- Jobs: `(status, available_at)`.

Use `EXPLAIN ANALYZE` with representative data before adding speculative indexes.

## 12. Data lifecycle and retention
Before real-world deployment, define retention for telemetry, uploaded files, audit events, sessions, and model artifacts. Expire/revoke sessions. Archive equipment instead of deleting records referenced by history. Provide a documented export and deletion process appropriate to the deployment's privacy obligations. Back up PostgreSQL and the file-storage directory together and test restoration.

## 13. Migration and seed strategy
- Alembic owns schema evolution.
- Review generated migrations; do not blindly accept autogeneration.
- Test upgrade from the previous supported revision and test backup/restore.
- Seed roles, permissions, equipment types, and a small knowledge-graph baseline.
- Keep demo organization and demo data in a clearly identifiable seed routine.
- Never seed a production default administrator password. Require secure bootstrap configuration and rotate it.

## 14. Initial implementation order
1. Users, roles, permissions, sessions.
2. Organizations and memberships.
3. Equipment types, equipment, specifications, components.
4. Sensors and readings.
5. Monitoring rules, anomalies, alerts.
6. ML models and predictions.
7. Knowledge nodes and edges.
8. Diagnoses and evidence.
9. Maintenance records.
10. Files, audit logs, background jobs.

This order supports a working end-to-end vertical slice while preserving the approved architecture.
