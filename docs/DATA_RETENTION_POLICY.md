# MechTech — Data Lifecycle and Retention Policy

**Document type:** Data Governance & Retention Policy  
**Status:** Approved  
**Version:** 1.0  

---

## 1. Principles of Data Retention

1. **Local-First & Resource Efficiency:** Avoid unbounded storage growth on local disks while maintaining longitudinal operational history.
2. **Immutable Evidence Integrity:** Never overwrite historical sensor readings or diagnostic evidence records used to support maintenance decisions.
3. **Soft Archival over Deletion:** Machinery referenced by historical telemetry and maintenance orders is soft-archived rather than deleted from relational tables.

---

## 2. Retention Schedules

| Data Category | Primary Storage | Retention Period | Compaction / Archival Strategy |
|:---|:---|:---:|:---|
| **High-Frequency Sensor Readings** | `sensor_readings` | 30 days raw | Downsampled into hourly statistical aggregates (mean, min, max, std dev) for historical trend visualization. |
| **Anomaly Events & Alerts** | `anomaly_events`, `alerts` | 1 year | Retained permanently in resolved/dismissed states with resolution notes. |
| **Diagnostic Snapshots & Evidence** | `diagnoses`, `diagnosis_evidence` | Indefinite | Permanent immutable snapshots with policy version and reviewer decisions. |
| **Maintenance Work Orders** | `maintenance_records` | Indefinite | Retained for equipment lifecycle tracking and audit compliance. |
| **Uploaded Attachments (PDFs, Images)** | `data/uploads` | 2 years | Cleaned up only when parent equipment or maintenance record is expunged. |
| **Security Audit Logs** | `audit_logs` | 1 year | Immutable append-only log; expunged upon explicit administrative retention review. |
| **User Sessions** | `user_sessions` | 12 hours | Revoked automatically on logout or expiration. |

---

## 3. Archival and Deletion Workflow

- **Equipment Deactivation:** Set `status = 'archived'`. Historical telemetry and work orders remain fully queryable for auditing.
- **Tenant Expungement:** If an organization is removed, cascading deletion cleanly purges associated records and triggers file unlinking in `data/uploads/{org_id}`.

