from app.core.config import settings

DATA_SUBDIRECTORIES: tuple[str, ...] = (
    "db",
    "models/anomaly",
    "models/classification",
    "datasets/generated",
    "datasets/evaluation",
    "exports",
    "backups",
    "logs",
)


def ensure_data_directories() -> None:
    for relative_path in DATA_SUBDIRECTORIES:
        (settings.data_root / relative_path).mkdir(parents=True, exist_ok=True)
