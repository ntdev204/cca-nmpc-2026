from __future__ import annotations

import argparse
import csv
import json
from types import SimpleNamespace
from pathlib import Path

import pytest

import tools.stm_experiment as stm


def test_make_pattern_has_strict_zero_tail() -> None:
    rows = stm.make_pattern(0.3, 0.1, "forward", 0.03, 0.15)
    assert rows[-1] == (0.3, 0.0, 0.0, 0.0)
    assert all(left[0] < right[0] for left, right in zip(rows, rows[1:]))


def test_schedule_and_safety_contracts(tmp_path: Path) -> None:
    schedule_path = tmp_path / "schedule.csv"
    schedule_path.write_text(
        "t_s,vx_mps,vy_mps,wz_radps\n0.0,0.02,0.0,0.0\n0.2,0.0,0.0,0.0\n",
        encoding="utf-8",
    )
    rows = stm.load_schedule(schedule_path)
    assert rows[-1][1:] == (0.0, 0.0, 0.0)
    safety_path = tmp_path / "safety.json"
    safety_path.write_text(
        json.dumps(
            {
                "approved": True,
                "emergency_stop_verified": True,
                "remote_disable_verified": True,
                "watchdog_verified": True,
            }
        ),
        encoding="utf-8",
    )
    assert stm.validate_safety_record(safety_path)["approved"] is True


def test_schedule_rejects_missing_zero_tail(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text(
        "t_s,vx_mps,vy_mps,wz_radps\n0.0,0.02,0.0,0.0\n0.2,0.01,0.0,0.0\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="zero-velocity"):
        stm.load_schedule(path)


def test_observe_run_writes_no_ros_manifest_and_zero_tail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeSource:
        def __init__(self, *args, **kwargs):
            self.latest = None
            self.sent: list[tuple[float, float, float]] = []

        def start(self) -> None:
            return None

        def send_velocity(self, vx: float, vy: float, wz: float) -> None:
            self.sent.append((vx, vy, wz))

        def stop(self) -> None:
            return None

    monkeypatch.setattr(stm, "Stm32SerialSource", FakeSource)
    output = tmp_path / "run"
    status = stm.run(
        argparse.Namespace(
            output=output,
            duration_s=0.06,
            period_s=0.02,
            schedule=None,
            pattern="observe",
            speed_mps=0.03,
            angular_radps=0.15,
            allow_actuation=False,
            safety_record=None,
            operator="test",
            firmware_id="fixture",
            map_json=None,
            port="fixture",
            baud=115200,
            timeout_s=0.01,
            mode=0,
        )
    )
    assert status == 0
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["runtime"]["ros_runtime"] is False
    assert manifest["physical_geometry_status"] == "pending_measurement"
    with (output / "control.csv").open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert rows[-1]["vx_cmd_mps"] == "0.0"
    assert rows[-1]["vy_cmd_mps"] == "0.0"
    assert rows[-1]["wz_cmd_radps"] == "0.0"


def test_stop_flag_forces_zero_before_next_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeSource:
        def __init__(self, *args, **kwargs):
            self.latest = SimpleNamespace(
                flag_stop=True,
                t_ns=1,
                vx_mps=0.0,
                vy_mps=0.0,
                wz_radps=0.0,
                accel_x_mps2=0.0,
                accel_y_mps2=0.0,
                accel_z_mps2=0.0,
                gyro_x_radps=0.0,
                gyro_y_radps=0.0,
                gyro_z_radps=0.0,
                voltage_v=0.0,
            )
            self.sent: list[tuple[float, float, float]] = []

        def start(self) -> None:
            return None

        def send_velocity(self, vx: float, vy: float, wz: float) -> None:
            self.sent.append((vx, vy, wz))

        def stop(self) -> None:
            return None

    monkeypatch.setattr(stm, "Stm32SerialSource", FakeSource)
    output = tmp_path / "stop-run"
    safety = tmp_path / "safety.json"
    safety.write_text(
        json.dumps(
            {
                "approved": True,
                "emergency_stop_verified": True,
                "remote_disable_verified": True,
                "watchdog_verified": True,
            }
        ),
        encoding="utf-8",
    )
    status = stm.run(
        argparse.Namespace(
            output=output,
            duration_s=0.2,
            period_s=0.02,
            schedule=None,
            pattern="forward",
            speed_mps=0.03,
            angular_radps=0.15,
            allow_actuation=True,
            safety_record=safety,
            operator="test",
            firmware_id="fixture",
            map_json=None,
            port="fixture",
            baud=115200,
            timeout_s=0.01,
            mode=0,
        )
    )
    assert status == 0
    with (output / "control.csv").open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert all(float(row["vx_cmd_mps"]) == 0.0 for row in rows)
    events = (output / "events.csv").read_text(encoding="utf-8")
    assert "stm_stop_latched" in events
