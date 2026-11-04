# MechTech Sensor Simulator

Local Python process that will generate timestamped temperature and vibration
readings for the prototype electric motor.

> All values are **simulated prototype data**, not physical sensor measurements.
> Vibration is a simplified normalized indicator, not calibrated mm/s RMS.

## Run (scaffold)

```powershell
.\.venv\Scripts\Activate.ps1
python -m simulator.simulator --scenario normal --interval 2 --seed 42
```

Scenarios: `normal`, `increased_vibration`, `overheating`,
`combined_abnormality`, `sensor_disconnection`, `noisy_sensor`,
`return_to_normal`.
