import hashlib
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib

from app.core.config import settings
from app.core.exceptions import AppError
from app.models import ModelRegistry

logger = logging.getLogger(__name__)


def models_root() -> Path:
    return (settings.data_root / "models").resolve()


def resolve_artifact_path(artifact_path: str) -> Path:
    path = Path(artifact_path)
    resolved = path.resolve() if path.is_absolute() else (settings.data_root / path).resolve()

    if not resolved.is_relative_to(models_root()):
        raise AppError(
            "The model artifact path is outside the trusted model directory.",
            code="ARTIFACT_PATH_INVALID",
            status_code=400,
        )
    if not resolved.is_file():
        raise AppError(
            "The model artifact does not exist.",
            code="ARTIFACT_MISSING",
            status_code=409,
        )
    return resolved


@lru_cache(maxsize=16)
def _load_joblib(path: str, checksum: str | None = None) -> Any:
    logger.info("Loading trusted model artifact: %s", path)
    return joblib.load(path)


def load_artifact(artifact_path: str) -> Any:
    resolved = resolve_artifact_path(artifact_path)
    return _load_joblib(str(resolved))


def artifact_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_registered_artifact(model_entry: ModelRegistry) -> Any:
    resolved = resolve_artifact_path(model_entry.artifact_path)
    checksum = artifact_sha256(resolved)
    if model_entry.artifact_sha256 and checksum != model_entry.artifact_sha256:
        raise AppError(
            "The registered model artifact failed its integrity check.",
            code="ARTIFACT_CHECKSUM_INVALID",
            status_code=409,
        )
    return _load_joblib(str(resolved), checksum)


def predict_classification(
    model: Any,
    feature_vector: list[float],
) -> tuple[str, dict[str, float], float]:
    probabilities = model.predict_proba([feature_vector])[0]
    classes = list(model.classes_)
    predicted = str(model.predict([feature_vector])[0])
    probability_map = {
        str(label): float(probability)
        for label, probability in zip(classes, probabilities, strict=True)
    }
    confidence = probability_map.get(predicted)
    return predicted, probability_map, float(confidence) if confidence is not None else 0.0
