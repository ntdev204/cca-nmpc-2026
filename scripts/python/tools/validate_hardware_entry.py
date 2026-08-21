from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone

UTC = timezone.utc
from pathlib import Path
from typing import Any

try:
    from tools._bootstrap import PROJECT_ROOT
except ModuleNotFoundError:
    from _bootstrap import PROJECT_ROOT


ROOT = PROJECT_ROOT
OUTPUT = Path("research/metadata/hardware/pr30_entry_preflight_20260813.json")
HEADER = Path("src/stm/firmware/protocol.h")
FIRMWARE_CONFIG = Path("src/stm/firmware/firmware_config.h")
FIRMWARE_README = Path("src/stm/firmware/README.md")
PACKAGER = Path("scripts/python/tools/final_pack.py")
TOOLS_README = Path("scripts/python/tools/README.md")
CAN_DECODER = Path("src/shared.py")
HARDWARE_BRIDGE = Path("src/hardware.py")
RECORDER = Path("scripts/python/tools/record_hardware.py")
DIRECT_STM_RECORDER = Path("scripts/python/tools/stm_experiment.py")
HARDWARE_ENTRY = Path("scripts/python/tools/hardware_entry.py")
STM_BRIDGE_SOURCE = Path("reference/robot/turn_on_rai_robot/src/rai_robot.cpp")
STM_BRIDGE_HEADER = Path("reference/robot/turn_on_rai_robot/include/turn_on_rai_robot/rai_robot.h")
CPP_STM_SOURCE = Path("src/control/src/stm_c_api.cpp")
CPP_STM_HEADER = Path("src/control/include/control/stm_c_api.h")
CPP_CAN_SOURCE = Path("src/control/src/can.cpp")
CPP_CAN_HEADER = Path("src/control/include/control/can.hpp")
MINI_MEC_URDF = Path("reference/robot/rai_robot_urdf/rai_robot_urdf/urdf/mini_mec_robot.urdf")
PHYSICAL_TEMPLATE = Path("configs/physical_experiment.template.yaml")
PHYSICAL_SPEC = Path("configs/physical_robot.json")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def current_hardware_packages(root: Path) -> list[str]:
    packages: list[str] = []
    for manifest_path in (root / "experiments" / "runs").rglob("manifest.json"):
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("capture_source") in {"hardware", "hardware_in_loop", "real_offline"}:
            packages.append(manifest_path.relative_to(root).as_posix())
    return sorted(packages)


def run_preflight(root: Path) -> dict[str, Any]:
    header = read(root / HEADER)
    firmware = read(root / FIRMWARE_CONFIG)
    firmware_readme = read(root / FIRMWARE_README)
    packager = read(root / PACKAGER)
    tools_readme = read(root / TOOLS_README)
    can_decoder = read(root / CAN_DECODER)
    hardware_bridge = read(root / HARDWARE_BRIDGE)
    recorder = read(root / RECORDER)
    direct_stm_recorder = read(root / DIRECT_STM_RECORDER)
    hardware_entry = read(root / HARDWARE_ENTRY)
    stm_bridge_source = read(root / STM_BRIDGE_SOURCE)
    stm_bridge_header = read(root / STM_BRIDGE_HEADER)
    cpp_stm_source = read(root / CPP_STM_SOURCE)
    cpp_stm_header = read(root / CPP_STM_HEADER)
    cpp_can_source = read(root / CPP_CAN_SOURCE)
    cpp_can_header = read(root / CPP_CAN_HEADER)
    mini_mec_urdf = read(root / MINI_MEC_URDF)
    template = read(root / PHYSICAL_TEMPLATE)
    physical_spec_path = root / PHYSICAL_SPEC
    physical_spec: dict[str, Any] = {}
    if physical_spec_path.is_file():
        try:
            parsed_spec = json.loads(physical_spec_path.read_text(encoding="utf-8"))
            if isinstance(parsed_spec, dict):
                physical_spec = parsed_spec
        except (OSError, json.JSONDecodeError):
            physical_spec = {}
    required_ids = {
        "command_header": "#define CCA_CAN_COMMAND_HEADER_ID  0x190u",
        "command_payload": "#define CCA_CAN_COMMAND_PAYLOAD_ID 0x191u",
        "status": "#define CCA_CAN_STATUS_ID          0x198u",
        "applied": "#define CCA_CAN_APPLIED_ID         0x199u",
        "wheels_abc": "#define CCA_CAN_WHEELS_ABC_ID      0x19Au",
        "wheel_d": "#define CCA_CAN_WHEEL_D_ID         0x19Bu",
    }
    checks = {
        name: value in header for name, value in required_ids.items()
    }
    checks.update(
        {
            "body_velocity_mode_declared": "CCA_MODE_BODY_VELOCITY" in header and "BODY_VELOCITY" in firmware_readme,
            "position_state_scope_declared": all(
                phrase in template
                for phrase in (
                    "control_mode: position_state",
                    "state_definition: [x_m, y_m, theta_rad, vx_mps, vy_mps, omega_radps]",
                )
            ) and "POSITION_STATE_FIELDS" in hardware_bridge,
            "legacy_torque_mode_not_claimed": "CCA_MODE_WHEEL_TORQUE" in header and "rejected" in firmware_readme.lower(),
            "commissioning_lock_zero": re.search(r"CCA_WHEEL_LOOP_COMMISSIONED\s+0u", firmware) is not None,
            "direct_csv_json_mapping": all(
                phrase in firmware_readme
                for phrase in ("control.csv", "robot_state.csv", "context.csv", "lidar.csv", "events.csv", "map.json")
            ),
            "python_can_decoder_present": "decode_cca_can_frame" in can_decoder and "cca_crc8" in can_decoder,
            "cpp_can_codec_present": all(
                phrase in cpp_can_source + cpp_can_header
                for phrase in ("CcaCanCrc8", "EncodeCcaBodyVelocityPayload", "DecodeCcaCanFrame")
            ),
            "cpp_can_c_abi_present": all(
                phrase in cpp_stm_source + cpp_stm_header
                for phrase in ("cca_can_crc8", "cca_can_encode_header", "cca_can_encode_body", "cca_can_decode")
            ),
            "python_cpp_can_selector_present": all(
                phrase in can_decoder
                for phrase in ("_CppCcaCanCodec", "_cpp_cca_can_codec", "CCA_CAN_BACKEND", "cpp_transport_library")
            ),
            "stm32_serial_bridge_present": all(
                phrase in hardware_bridge
                for phrase in ("STM32_FRAME_HEADER", "Stm32FrameDecoder", "Stm32SerialSource", "encode_stm32_velocity_command")
            ),
            "stm_bridge_frame_contract_referenced": all(
                phrase in stm_bridge_source for phrase in ("Stm32_Serial", "Cmd_Vel_Callback", "Get_Sensor_Data_New")
            ),
            "stm_bridge_frame_constants_present": all(
                phrase in stm_bridge_header for phrase in ("FRAME_HEADER", "FRAME_TAIL", "RECEIVE_DATA_SIZE", "SEND_DATA_SIZE")
            ),
            "cpp_stm_transport_present": all(
                phrase in cpp_stm_source + cpp_stm_header
                for phrase in ("cca_stm_open", "cca_stm_send_velocity", "cca_stm_read", "cca_stm_send_zero", "cca_stm_close")
            ),
            "mini_mec_urdf_present": all(
                phrase in mini_mec_urdf for phrase in ("mini_mec_robot", "lf_wheel_joint", "rf_wheel_joint", "camera_joint", "laser_joint")
            ),
            "record_actuation_gate_present": all(
                phrase in recorder for phrase in ("--command-csv", "--allow-actuation", "transport=stm32_serial")
            ),
            "motion_safety_record_gate_present": all(
                phrase in recorder for phrase in ("--safety-record", "validate_safety_record", "motion requires --safety-record")
            ) and all(
                phrase in hardware_entry for phrase in ("--safety-record", "motion requires --safety-record")
            ),
            "direct_stm_recorder_present": all(
                phrase in direct_stm_recorder
                for phrase in (
                    "Stm32SerialSource",
                    "robot_state.csv",
                    "control.csv",
                    "manifest.json",
                    "--allow-actuation",
                    "--safety-record",
                    "source.send_velocity(0.0, 0.0, 0.0)",
                )
            ),
            "single_hardware_entrypoint_present": all(
                phrase in hardware_entry
                for phrase in ("def robot_spec", "def prepare", "def schedule", "def preflight", "def record", "rai_robot_urdf")
            ),
            "no_device_preflight_present": all(
                phrase in hardware_entry
                for phrase in ("def _capture_preflight", '"devices_opened": False', "def record(args")
            ),
            "complete_urdf_inventory_present": all(
                phrase in hardware_entry
                for phrase in ("def urdf_catalog", "urdf_catalog()", '"available_urdf_models"')
            ),
            "sensor_contract_inventory_present": all(
                phrase in hardware_entry
                for phrase in ("def xacro_sensor_contract", '"xacro_sensor_contract"', '"simulation_only": True')
            ),
            "component_inventory_present": all(
                phrase in hardware_entry
                for phrase in ('"components"', '"wheels"', '"sensors"', '"link_masses_kg"')
            ),
            "footprint_contract_present": all(
                phrase in hardware_entry for phrase in ("def planar_footprint", '"footprint"', '"footprint_radius_m"')
            ),
            "runtime_urdf_geometry_metadata_present": all(
                phrase in recorder
                for phrase in ('"robot_geometry"', '"urdf_sha256"', '"wheel_radius_m"', '"footprint"')
            ),
            "runtime_urdf_source_hash_validation_present": all(
                phrase in recorder for phrase in ("def validate_robot_source", "sha256_path", "xacro hash")
            ),
            "no_ros_runtime_dependency": "no ros/ros 2" in tools_readme.lower() and "runtime dependency" in tools_readme.lower() and "middleware log" in firmware_readme.lower(),
            "packager_context_only": '"context_only": True' in packager and '"human_trajectory_generated": False' in packager,
            "calibration_sidecar_contract": "calibration.json" in packager and "calibration.json" in tools_readme,
            "physical_template_planned": "status: planned" in template and "stage: H0" in template,
            "physical_template_unapproved": "approved: false" in template and "emergency_stop_verified: false" in template,
            "physical_spec_recorded": (
                physical_spec.get("schema") == "cca-physical-robot-v1"
                and physical_spec.get("status") == "measured"
                and physical_spec.get("robot_model") == "mini_mec_robot"
                and isinstance(physical_spec.get("sensor_mounts"), dict)
            ),
        }
    )
    packages = current_hardware_packages(root)
    errors = [name for name, passed in checks.items() if not passed]
    admission_reasons = []
    if not packages:
        admission_reasons.append("no sealed direct hardware/hardware-in-loop/real-offline package exists")
    if checks["commissioning_lock_zero"]:
        admission_reasons.append("STM wheel-loop commissioning remains locked at zero")
    admission_reasons.append("physical experiment template is planned H0 with safety approval pending")
    if checks["physical_spec_recorded"]:
        admission_reasons.append(
            "user-supplied physical geometry is recorded; independent dimensional verification, sensor calibration and ground truth remain pending"
        )
    else:
        admission_reasons.append("robot physical specifications, sensor calibration and independent ground truth are absent")
    admission_reasons.append("no stage-gate, protocol-freeze or target-hardware manifest is approved")
    source_paths = [
        HEADER,
        FIRMWARE_CONFIG,
        FIRMWARE_README,
        PACKAGER,
        TOOLS_README,
        CAN_DECODER,
        HARDWARE_BRIDGE,
        RECORDER,
        DIRECT_STM_RECORDER,
        HARDWARE_ENTRY,
        STM_BRIDGE_SOURCE,
        STM_BRIDGE_HEADER,
        CPP_STM_SOURCE,
        CPP_STM_HEADER,
        CPP_CAN_SOURCE,
        CPP_CAN_HEADER,
        MINI_MEC_URDF,
        PHYSICAL_TEMPLATE,
        PHYSICAL_SPEC,
    ]
    return {
        "schema": "cca-pr30-hardware-entry-preflight-v1",
        "checked_at_utc": utc_now(),
        "paper_edit": False,
        "status": "PASS" if not errors else "FAIL",
        "admission_status": "BLOCKED" if admission_reasons else "READY_FOR_REVIEW",
        "checks": checks,
        "errors": errors,
        "admission_reasons": admission_reasons,
        "hardware_packages": packages,
        "sources": {
            path.as_posix(): {"sha256": sha256_file(root / path)} for path in source_paths
        },
        "next_actions": [
            (
                "independently verify supplied robot physical and sensor specifications"
                if checks["physical_spec_recorded"]
                else "supply robot physical and sensor specifications"
            ),
            "approve H0 safety, stop rules and target-hardware manifest",
            "commission and verify e-stop/watchdog/wheel signs before motion",
            "capture and seal direct CSV/JSON package with final_pack.py",
        ],
        "tool": {
            "path": Path(__file__).resolve().relative_to(root).as_posix(),
            "sha256": sha256_file(Path(__file__).resolve()),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    root = args.workspace_root.resolve()
    report = run_preflight(root)
    output = (root / args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
