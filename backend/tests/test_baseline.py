from types import SimpleNamespace

import pytest

from app.ml.baseline import activate_baseline, compare_features, fit_baseline, save_baseline
from app.ml.features import FEATURE_NAMES


def _normal_rows() -> list[dict[str, float]]:
    rows = []
    for offset in (0.0, 0.01, -0.01):
        rows.append(
            {
                name: (10.0 if name == "count" else index * 0.1 + offset)
                for index, name in enumerate(FEATURE_NAMES)
            }
        )
    return rows


def _profile(rows: list[dict[str, float]]):
    values = fit_baseline(
        rows,
        scenario_labels=["normal"] * len(rows),
        baseline_name="test",
        baseline_version="1.0.0",
        dataset_description="deterministic normal-only fixture",
        z_threshold=3.0,
    )
    return SimpleNamespace(
        baseline_version=values["baseline_version"],
        feature_schema_version=values["feature_schema_version"],
        means_json=values["means_json"],
        standard_deviations_json=values["standard_deviations_json"],
        z_threshold=values["z_threshold"],
        values=values,
    )


def test_baseline_is_fit_only_from_normal_and_returns_explainable_evidence() -> None:
    rows = _normal_rows()
    profile = _profile(rows)

    normal = compare_features(rows[0], profile)
    assert normal.is_anomaly is False
    assert normal.detector_name == "statistical_baseline"

    unusual = dict(rows[0])
    unusual["temperature_mean"] += 5.0
    result = compare_features(unusual, profile)
    assert result.is_anomaly is True
    evidence = result.evidence["temperature_mean"]
    assert evidence["measured_value"] == unusual["temperature_mean"]
    assert evidence["baseline_mean"] == pytest.approx(profile.means_json["temperature_mean"])
    assert evidence["deviation"] > 0
    assert evidence["rule"] == "absolute_z_score_exceeds_threshold"

    with pytest.raises(ValueError, match="normal windows"):
        fit_baseline(
            rows,
            scenario_labels=["normal", "overheating", "normal"],
            baseline_name="unsafe",
            baseline_version="1",
            dataset_description="must reject abnormal data",
            z_threshold=3.0,
        )


def test_zero_variance_baseline_uses_explicit_deviation_rule() -> None:
    rows = [dict.fromkeys(FEATURE_NAMES, 1.0) for _ in range(2)]
    profile = _profile(rows)
    changed = dict(rows[0])
    changed["vibration_mean"] = 1.1

    result = compare_features(changed, profile)
    evidence = result.evidence["vibration_mean"]
    assert result.is_anomaly is True
    assert evidence["z_score"] is None
    assert evidence["rule"] == "nonzero_deviation_from_zero_variance_baseline"


def test_baseline_version_is_persisted_and_activation_is_explicit(db_session) -> None:
    profile = _profile(_normal_rows())
    saved = save_baseline(db_session, profile.values)
    assert saved.is_active is False

    active = activate_baseline(db_session, saved)
    assert active.is_active is True
