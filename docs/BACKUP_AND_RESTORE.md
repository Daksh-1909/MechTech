# MechTech — Backup and Disaster Recovery Runbook

**Document type:** Operational Runbook & Disaster Recovery  
**Status:** Approved  
**Version:** 1.0  

---

## 1. Overview & Scope

MechTech operates with a local-first, modular architecture. A complete system backup encompasses three essential components:

1. **Relational Database:** Configuration, users, organizations, equipment, telemetry readings, alerts, diagnostic evidence, and maintenance records.
2. **File Storage Volume (`data/uploads`):** PDF vibration reports, inspection photos, and maintenance documentation attachments.
3. **Model Registry (`data/models`):** Trained scikit-learn model bundles, version metadata, and evaluation metrics.

Both SQLite (development/demonstration) and PostgreSQL (production) environments are supported.

---

## 2. Backup Procedure

### Automated Backup Execution

Run the automated backup script from the repository root:

```bash
python backend/scripts/backup.py
```

Optional custom target directory:
```bash
python backend/scripts/backup.py --dest /var/backups/mechtech
```

### What Happens During Backup
1. **Online Non-blocking Snapshot:** Uses the SQLite Online Backup API (or `pg_dump` in PostgreSQL) to take a consistent snapshot without shutting down the server.
2. **File & Artifact Collection:** Copies all uploaded documents and model artifacts to staging.
3. **Cryptographic Manifest Generation:** Computes SHA-256 hashes for every file and stores them in `manifest.json`.
4. **Archive Packaging:** Compresses into a single timestamped archive:  
   `mechtech_backup_YYYYMMDD_HHMMSSZ.tar.gz`.

---

## 3. Restore Procedure

### Step-by-Step Restoration

1. **Stop Application Services (optional for clean restore):**
   ```bash
   docker compose down
   # or stop local uvicorn process
   ```

2. **Execute Restore Utility:**
   ```bash
   python backend/scripts/restore.py /path/to/mechtech_backup_20261113_120000Z.tar.gz --force
   ```

3. **Restoration Verification Steps:**
   - **Checksum Verification:** The restore script automatically verifies the SHA-256 checksum of every extracted file against `manifest.json`. If any file has been modified or corrupted, restoration terminates immediately before touching production data.
   - **Database Readiness:** Checks connection readiness via `GET /health/ready`.
   - **Asset Integrity:** Verifies that uploaded files and models are restored with correct permissions.

4. **Restart Services & Validate:**
   ```bash
   curl -s http://127.0.0.1:8000/api/v1/health/ready
   # Expected response: {"status": "ready"}
   ```

---

## 4. Disaster Recovery Scenarios

| Failure Scenario | Mitigation | Recovery Target |
|:---|:---|:---|
| **Host storage failure** | Offsite / secondary volume sync of `.tar.gz` | RTO < 15 min, RPO < backup interval |
| **Corrupted database** | Re-run restore script with latest verified archive | RTO < 5 min |
| **Accidental equipment deletion** | Restore to temporary database, export entity, import | RTO < 30 min |

---

## 5. Retention & Automation Recommendation

In production deployment:
- Execute `backup.py` daily via cron job (`0 2 * * *`).
- Retain daily backups for 14 days, weekly backups for 8 weeks, monthly backups for 12 months.
- Prune backups older than the retention window.

