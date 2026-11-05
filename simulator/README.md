# MechTech Sensor Simulator

Local Python process that will generate timestamped temperature and vibration
readings for the prototype electric motor.

> All values are **simulated prototype data**, not physical sensor measurements.
> Vibration is a simplified normalized indicator, not calibrated mm/s RMS.

## Run continuous ingestion

```powershell
.\.venv\Scripts\Activate.ps1
python -m simulator.simulator --scenario normal --interval 2 --seed 42
```

Generate a deterministic five-scenario dataset without starting the API:

```powershell
python -m simulator.simulator --export-csv data/exports/phase3.csv --samples-per-scenario 120 --seed 42
```

Continuous runs accept a stop event through the Python API and flush any
partial batch before returning. Ingestion uses the same backend validation and
idempotency rules as API clients.

Scenarios: `normal`, `increased_vibration`, `overheating`,
`combined_abnormality`, `sensor_disconnection`, `noisy_sensor`,
`return_to_normal`.

The Phase 3 labeled training dataset uses `normal`, `excessive_vibration`,
`overheating`, `bearing_abnormality`, and `combined_abnormality`. These are
software test patterns, not validated physical fault signatures. The default
vibration channel is a simplified `simulated_index` and must not be reported
as mm/s RMS.
