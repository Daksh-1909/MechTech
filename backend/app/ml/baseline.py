"""Transparent statistical baseline fitting and deviation reporting."""

import math
from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.time import utcnow
from app.ml.features import FEATURE_NAMES, FEATURE_SCHEMA_VERSION
from app.models import BaselineProfile


@dataclass(frozen=True, slots=True)
class BaselineResult:
    is_anomaly: bool
    detector_name: str
    baseline_version: str
    threshold: float
    evidence: dict[str, dict[str, float | str | None]]


def fit_baseline(
    feature_rows: Iterable[dict[str, float]],
    *,
    scenario_labels: Iterable[str],
    baseline_name: str,
    baseline_version: str,
    dataset_description: str,
    z_threshold: float,
) -> dict:
    """Fit population means/stds from explicitly supplied normal-only windows."""
    rows = list(feature_rows)
    labels = list(scenario_labels)
    if len(rows) < 2:
        raise ValueError("At least two normal training windows are required.")
    if len(labels) != len(rows) or any(label != "normal" for label in labels):
        raise ValueError("Statistical baselines may be fitted only from labeled normal windows.")
    if not math.isfinite(z_threshold) or z_threshold <= 0:
        raise ValueError("z_threshold must be a positive finite number.")
    for index, row in enumerate(rows):
        missing = [name for name in FEATURE_NAMES if name not in row]
        if missing:
            raise ValueError(f"Training window {index} is missing features: {', '.join(missing)}")
        if not all(math.isfinite(float(row[name])) for name in FEATURE_NAMES):
            raise ValueError(f"Training window {index} contains non-finite values.")
    means = {name: sum(float(row[name]) for row in rows) / len(rows) for name in FEATURE_NAMES}
    standard_deviations = {
        name: math.sqrt(sum((float(row[name]) - means[name]) ** 2 for row in rows) / len(rows))
        for name in FEATURE_NAMES
    }
    return {
        "baseline_name": baseline_name,
        "baseline_version": baseline_version,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "training_sample_count": len(rows),
        "training_dataset_description": dataset_description[:500],
        "means_json": means,
        "standard_deviations_json": standard_deviations,
        "z_threshold": z_threshold,
    }


def save_baseline(db: Session, values: dict) -> BaselineProfile:
    existing = db.scalar(
        select(BaselineProfile).where(
            BaselineProfile.baseline_name == values["baseline_name"],
            BaselineProfile.baseline_version == values["baseline_version"],
        )
    )
    if existing is not None:
        raise AppError(
            "This baseline version already exists.", code="BASELINE_EXISTS", status_code=409
        )
    profile = BaselineProfile(**values, created_at=utcnow(), is_active=False)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def activate_baseline(db: Session, profile: BaselineProfile) -> BaselineProfile:
    db.query(BaselineProfile).filter(BaselineProfile.is_active.is_(True)).update(
        {BaselineProfile.is_active: False}, synchronize_session=False
    )
    profile.is_active = True
    db.commit()
    db.refresh(profile)
    return profile


def get_active_baseline(db: Session) -> BaselineProfile | None:
    return db.scalar(
        select(BaselineProfile)
        .where(BaselineProfile.is_active.is_(True))
        .order_by(BaselineProfile.id.desc())
        .limit(1)
    )


def compare_features(
    features: dict[str, float],
    profile: BaselineProfile,
) -> BaselineResult:
    if profile.feature_schema_version != FEATURE_SCHEMA_VERSION:
        raise AppError(
            "The active statistical baseline uses an incompatible feature schema.",
            code="BASELINE_SCHEMA_MISMATCH",
            status_code=409,
        )
    means = profile.means_json
    stds = profile.standard_deviations_json
    missing = [name for name in FEATURE_NAMES if name not in features or name not in means]
    if missing:
        raise AppError(
            f"Features are missing baseline values: {', '.join(missing)}",
            code="BASELINE_FEATURES_MISSING",
            status_code=422,
        )

    evidence: dict[str, dict[str, float | str | None]] = {}
    triggered = False
    for name in FEATURE_NAMES:
        if name == "count":
            continue
        value = float(features[name])
        mean = float(means[name])
        standard_deviation = float(stds[name])
        if not all(math.isfinite(number) for number in (value, mean, standard_deviation)):
            raise AppError(
                "Baseline inputs must be finite.", code="INVALID_FEATURES", status_code=422
            )
        deviation = value - mean
        if standard_deviation == 0:
            z_score = None
            is_triggered = deviation != 0
            rule = "nonzero_deviation_from_zero_variance_baseline"
        else:
            z_score = deviation / standard_deviation
            is_triggered = abs(z_score) > profile.z_threshold
            rule = "absolute_z_score_exceeds_threshold"
        if is_triggered:
            triggered = True
        evidence[name] = {
            "measured_value": value,
            "baseline_mean": mean,
            "baseline_standard_deviation": standard_deviation,
            "deviation": deviation,
            "z_score": z_score,
            "rule": rule if is_triggered else "within_configured_baseline",
        }
    return BaselineResult(
        is_anomaly=triggered,
        detector_name="statistical_baseline",
        baseline_version=profile.baseline_version,
        threshold=profile.z_threshold,
        evidence=evidence,
    )
