"""Create, verify and restore SQLite-consistent backups."""

import argparse
import os
import sqlite3
import sys
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.core.paths import ensure_data_directories


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MechTech SQLite backup and restore utility.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup = subparsers.add_parser("backup", help="Create a consistent SQLite backup.")
    backup.add_argument("--source")
    backup.add_argument("--output")

    restore = subparsers.add_parser("restore", help="Restore a verified SQLite backup.")
    restore.add_argument("--backup", required=True)
    restore.add_argument("--target")
    restore.add_argument("--force", action="store_true")

    verify = subparsers.add_parser("verify", help="Run SQLite integrity checks.")
    verify.add_argument("--path", required=True)
    return parser


def database_path() -> Path:
    prefix = "sqlite:///"
    if not settings.database_url.startswith(prefix):
        raise ValueError("Backup and restore require a SQLite DATABASE_URL.")
    return Path(settings.database_url[len(prefix) :])


def verify_database(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(path)
    with closing(sqlite3.connect(path)) as connection:
        rows = connection.execute("PRAGMA integrity_check").fetchall()
    result = "; ".join(str(row[0]) for row in rows)
    if result != "ok":
        raise ValueError(f"SQLite integrity check failed: {result}")
    return result


def backup_database(source: Path, destination: Path) -> dict[str, object]:
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with (
        closing(sqlite3.connect(source)) as source_connection,
        closing(sqlite3.connect(destination)) as destination_connection,
    ):
        source_connection.backup(destination_connection)
    integrity = verify_database(destination)
    return {
        "source": str(source),
        "destination": str(destination),
        "bytes": destination.stat().st_size,
        "integrity_check": integrity,
    }


def restore_database(backup: Path, target: Path, *, force: bool = False) -> dict[str, object]:
    if target.exists() and not force:
        raise FileExistsError(f"{target} already exists; pass --force to replace it.")
    verify_database(backup)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.stem}-restore-{uuid4().hex}.db")
    try:
        with (
            closing(sqlite3.connect(backup)) as backup_connection,
            closing(sqlite3.connect(temporary)) as temporary_connection,
        ):
            backup_connection.backup(temporary_connection)
        verify_database(temporary)
        for suffix in ("-wal", "-shm"):
            sidecar = Path(f"{target}{suffix}")
            if sidecar.exists():
                sidecar.unlink()
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()
    return {
        "backup": str(backup),
        "target": str(target),
        "bytes": target.stat().st_size,
        "integrity_check": verify_database(target),
    }


def _default_output() -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return settings.data_root / "backups" / f"mechtech-{timestamp}.db"


def main() -> int:
    args = build_parser().parse_args()
    ensure_data_directories()

    try:
        if args.command == "backup":
            source = Path(args.source) if args.source else database_path()
            destination = Path(args.output) if args.output else _default_output()
            report = backup_database(source, destination)
            print(f"Backup created: {report['destination']} ({report['bytes']} bytes)")
            print(f"Integrity: {report['integrity_check']}")
        elif args.command == "restore":
            target = Path(args.target) if args.target else database_path()
            report = restore_database(Path(args.backup), target, force=args.force)
            print(f"Restored: {report['target']} ({report['bytes']} bytes)")
            print(f"Integrity: {report['integrity_check']}")
        else:
            print(f"Integrity: {verify_database(Path(args.path))}")
    except (FileExistsError, FileNotFoundError, ValueError, OSError) as exc:
        print(f"Backup/restore failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
