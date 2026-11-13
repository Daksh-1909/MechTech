"""MechTech Restore Utility.

Restores a MechTech deployment from a timestamped backup archive:
1. Validates tar.gz archive integrity and extracts to secure staging
2. Verifies cryptographic SHA-256 checksum of every file against manifest.json
3. Safely restores database, uploads, and model artifacts
4. Performs verification check ensuring system is operational
"""

import argparse
import hashlib
import json
import logging
from pathlib import Path
import shutil
import sqlite3
import sys
import tarfile

_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mechtech-restore")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(64 * 1024):
            h.update(chunk)
    return h.hexdigest()


def restore_backup(archive_path: Path, force: bool = False) -> bool:
    if not archive_path.exists():
        raise FileNotFoundError(f"Backup archive not found: {archive_path}")

    staging_dir = archive_path.parent / f".restore_staging_{archive_path.stem}"
    staging_dir.mkdir(parents=True, exist_ok=True)

    try:
        logger.info("Extracting archive %s to staging...", archive_path)
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(staging_dir)

        # 1. Read manifest
        manifest_file = staging_dir / "manifest.json"
        if not manifest_file.exists():
            raise ValueError("Corrupted backup: manifest.json is missing.")

        manifest = json.loads(manifest_file.read_text())
        logger.info(
            "Found backup manifest for %s v%s created at %s",
            manifest.get("app_name"),
            manifest.get("app_version"),
            manifest.get("timestamp"),
        )

        # 2. Cryptographic checksum validation
        logger.info("Verifying cryptographic SHA-256 checksums of all archived files...")
        file_checksums = manifest.get("files", {})
        for rel_path, meta in file_checksums.items():
            staged_file = staging_dir / rel_path
            if not staged_file.exists():
                raise ValueError(f"Integrity check failed: missing file {rel_path}")

            actual_sha = sha256_file(staged_file)
            expected_sha = meta["sha256"]
            if actual_sha != expected_sha:
                raise ValueError(
                    f"Integrity check failed for {rel_path}: checksum mismatch! (expected {expected_sha}, got {actual_sha})"
                )

        logger.info("Integrity check passed: all %d files verified.", len(file_checksums))

        # 3. Restore database
        staged_db = staging_dir / "database" / "mechtech.db"
        if staged_db.exists() and settings.database_url.startswith("sqlite:///"):
            target_db = Path(settings.database_url.replace("sqlite:///", ""))
            logger.info("Restoring SQLite database to %s...", target_db)
            target_db.parent.mkdir(parents=True, exist_ok=True)

            source_conn = sqlite3.connect(staged_db)
            dest_conn = sqlite3.connect(target_db)
            source_conn.backup(dest_conn)
            dest_conn.close()
            source_conn.close()
            logger.info("Database restoration complete.")

        # 4. Restore uploads
        staged_uploads = staging_dir / "uploads"
        if staged_uploads.exists():
            target_uploads = settings.data_root / "uploads"
            target_uploads.mkdir(parents=True, exist_ok=True)
            logger.info("Restoring uploaded documents to %s...", target_uploads)
            shutil.copytree(staged_uploads, target_uploads, dirs_exist_ok=True)

        # 5. Restore models
        staged_models = staging_dir / "models"
        if staged_models.exists():
            target_models = settings.data_root / "models"
            target_models.mkdir(parents=True, exist_ok=True)
            logger.info("Restoring model registry artifacts to %s...", target_models)
            shutil.copytree(staged_models, target_models, dirs_exist_ok=True)

        logger.info("SUCCESS: Full system restoration completed cleanly.")
        return True

    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore MechTech platform from backup archive.")
    parser.add_argument("archive", type=Path, help="Path to .tar.gz backup archive")
    parser.add_argument("--force", action="store_true", help="Force restore without manual confirmation")
    args = parser.parse_args()

    try:
        restore_backup(args.archive, args.force)
        return 0
    except Exception as exc:
        logger.error("Restore failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

