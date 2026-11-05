from enum import StrEnum


class Scenario(StrEnum):
    """Supported prototype simulation scenarios (aligned with the requirements)."""

    NORMAL = "normal"
    EXCESSIVE_VIBRATION = "excessive_vibration"
    BEARING_ABNORMALITY = "bearing_abnormality"
    INCREASED_VIBRATION = "increased_vibration"
    OVERHEATING = "overheating"
    COMBINED_ABNORMALITY = "combined_abnormality"
    SENSOR_DISCONNECTION = "sensor_disconnection"
    NOISY_SENSOR = "noisy_sensor"
    RETURN_TO_NORMAL = "return_to_normal"


# All ranges are prototype simulation settings, not motor safety limits.
# Vibration is a simplified normalized indicator, not calibrated mm/s RMS.
NORMAL_RANGES: dict[str, tuple[float, float]] = {
    "temperature_c": (45.0, 60.0),
    "vibration_normalized": (0.10, 0.30),
}

SCENARIO_RANGES: dict[Scenario, dict[str, tuple[float, float]]] = {
    Scenario.NORMAL: NORMAL_RANGES,
    Scenario.EXCESSIVE_VIBRATION: {
        "temperature_c": (45.0, 62.0),
        "vibration_normalized": (0.65, 1.00),
    },
    Scenario.BEARING_ABNORMALITY: {
        "temperature_c": (55.0, 72.0),
        "vibration_normalized": (0.45, 0.90),
    },
    Scenario.INCREASED_VIBRATION: {
        "temperature_c": (45.0, 62.0),
        "vibration_normalized": (0.65, 1.00),
    },
    Scenario.OVERHEATING: {
        "temperature_c": (85.0, 110.0),
        "vibration_normalized": (0.10, 0.30),
    },
    Scenario.COMBINED_ABNORMALITY: {
        "temperature_c": (85.0, 110.0),
        "vibration_normalized": (0.65, 1.00),
    },
    Scenario.NOISY_SENSOR: {
        "temperature_c": (45.0, 60.0),
        "vibration_normalized": (0.10, 0.30),
    },
    Scenario.RETURN_TO_NORMAL: NORMAL_RANGES,
}
