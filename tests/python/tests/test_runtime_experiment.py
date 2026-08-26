from __future__ import annotations

import json
from types import SimpleNamespace

from runtime import experiment


def test_runtime_experiment_records_filtered_state_without_actuation(tmp_path, monkeypatch) -> None:
    class FakeSource:
        def __init__(self, *args, **kwargs) -> None:
            self.latest = SimpleNamespace(
                t_ns=1,
                flag_stop=0,
                vx_mps=0.1,
                vy_mps=0.0,
                wz_radps=0.0,
                accel_x_mps2=0.0,
                accel_y_mps2=0.0,
                accel_z_mps2=0.0,
                gyro_x_radps=0.0,
                gyro_y_radps=0.0,
                gyro_z_radps=0.0,
                voltage_v=12.0,
            )
            self.last_command = None

        def start(self) -> None:
            return None

        def send_velocity(self, vx, vy, wz) -> None:
            self.last_command = (0, vx, vy, wz)

        def stop(self) -> None:
            return None

    monkeypatch.setattr(experiment, "Stm32SerialSource", FakeSource)
    output = tmp_path / "run"
    runner = experiment.StmExperiment("fixture")
    assert runner.run(output=output, duration_s=0.01, period_s=0.01) == 0
    header = (output / "robot_state.csv").read_text(encoding="utf-8").splitlines()[0]
    assert "state_estimator" in header
    rows = (output / "robot_state.csv").read_text(encoding="utf-8").splitlines()
    assert len(rows) == 2
    metadata = json.loads((output / "capture.json").read_text(encoding="utf-8"))
    assert metadata["state_estimator"] == "six_state_ekf"
