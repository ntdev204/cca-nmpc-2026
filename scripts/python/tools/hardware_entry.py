from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from datetime import datetime, timezone

UTC = timezone.utc
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

try:
    from tools._bootstrap import PROJECT_ROOT
except ModuleNotFoundError:
    from _bootstrap import PROJECT_ROOT


ROOT = PROJECT_ROOT
REFERENCE_ROOT = ROOT / "reference" / "robot"
URDF_PACKAGE = REFERENCE_ROOT / "rai_robot_urdf" / "rai_robot_urdf"
PACKAGE_XML = URDF_PACKAGE / "package.xml"
PACKAGE_CMAKE = URDF_PACKAGE / "CMakeLists.txt"
URDF = URDF_PACKAGE / "urdf" / "mini_mec_robot.urdf"
XACRO = REFERENCE_ROOT / "turn_on_rai_robot" / "urdf" / "mini_mec_gazebo.urdf.xacro"
UDEV = REFERENCE_ROOT / "turn_on_rai_robot" / "rai_udev.sh"
MESH_ROOT = URDF_PACKAGE / "meshes"
PROFILE = "n10p-108b-v1"
STATE = ["x_m", "y_m", "theta_rad", "vx_mps", "vy_mps", "omega_radps"]


def sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_xyz(value: str | None) -> list[float]:
    if not value:
        raise ValueError("URDF joint origin is missing xyz")
    values = [float(item) for item in value.split()]
    if len(values) != 3 or not all(math.isfinite(item) for item in values):
        raise ValueError("URDF joint origin xyz is invalid")
    return values


def parse_rpy(value: str | None) -> list[float]:
    if not value:
        return [0.0, 0.0, 0.0]
    values = [float(item) for item in value.split()]
    if len(values) != 3 or not all(math.isfinite(item) for item in values):
        raise ValueError("URDF joint origin rpy is invalid")
    return values


def stl_bounds(path: Path, *, units: str) -> dict[str, Any]:
    import struct

    payload = path.read_bytes()
    if len(payload) < 84:
        raise ValueError(f"STL is too short: {path}")
    count = struct.unpack_from("<I", payload, 80)[0]
    expected = 84 + 50 * count
    if len(payload) < expected:
        raise ValueError(f"binary STL is truncated: {path}")
    vertices: list[tuple[float, float, float]] = []
    for index in range(count):
        offset = 84 + index * 50 + 12
        values = struct.unpack_from("<9f", payload, offset)
        vertices.extend((tuple(values[0:3]), tuple(values[3:6]), tuple(values[6:9])))
    if not vertices:
        raise ValueError(f"STL has no triangles: {path}")
    axes = tuple(zip(*vertices))
    minimum = [min(axis) for axis in axes]
    maximum = [max(axis) for axis in axes]
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "triangles": count,
        "units": units,
        "min": minimum,
        "max": maximum,
        "span": [high - low for low, high in zip(minimum, maximum)],
    }


def mesh_inventory() -> dict[str, Any]:
    mini = MESH_ROOT / "mini_mec_robot_meshes"
    names = (
        "base_link.STL",
        "controller_link.STL",
        "lf_wheel_link.STL",
        "lb_wheel_link.STL",
        "rf_wheel_link.STL",
        "rb_wheel_link.STL",
        "camera_link.STL",
        "laser.STL",
    )
    stl = {name: stl_bounds(mini / name, units="m") for name in names}
    sensors = {}
    for name in ("astra.dae", "lds.stl", "r200.dae"):
        path = MESH_ROOT / "sensors" / name
        sensors[name] = {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
            "format": path.suffix.lower().lstrip("."),
        }
        if path.suffix.lower() == ".stl":
            sensors[name].update(stl_bounds(path, units="asset_units_unknown"))
    return {"mini_mec_robot": stl, "sensor_library": sensors}


def urdf_catalog() -> dict[str, Any]:
    models: dict[str, Any] = {}
    for path in sorted((URDF_PACKAGE / "urdf").glob("*.urdf")):
        root = ElementTree.parse(path).getroot()
        links = [link.attrib.get("name", "") for link in root.findall("link")]
        joints = [joint.attrib.get("name", "") for joint in root.findall("joint")]
        wheel_links = sorted(name for name in links if "wheel" in name.lower())
        sensor_links = sorted(
            name
            for name in links
            if any(token in name.lower() for token in ("camera", "laser", "lidar", "imu", "sensor"))
        )
        models[path.stem] = {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256(path),
            "links": len(links),
            "joints": len(joints),
            "wheel_links": wheel_links,
            "sensor_links": sensor_links,
        }
    return {"count": len(models), "models": models}


def xacro_sensor_contract() -> dict[str, Any]:
    text = XACRO.read_text(encoding="utf-8")

    def value(pattern: str, cast: Any) -> Any:
        match = re.search(pattern, text, flags=re.DOTALL)
        if match is None:
            raise ValueError(f"xacro sensor contract field is missing: {pattern}")
        return cast(match.group(1))

    lidar_block = r'<sensor type="ray" name="laser_sensor">'
    camera_block = r'<sensor type="camera" name="camera_sensor">'
    depth_block = r'<sensor type="depth" name="depth_sensor">'
    imu_block = r'<sensor name="imu_sensor" type="imu">'

    def block_value(block: str, tag: str, cast: Any) -> Any:
        pattern = rf"{block}.*?<\s*{tag}\s*>([^<]+)<\s*/\s*{tag}\s*>"
        match = re.search(pattern, text, flags=re.DOTALL)
        if match is None:
            raise ValueError(f"xacro sensor contract field is missing: {pattern}")
        return cast(match.group(1))

    return {
        "source": XACRO.relative_to(ROOT).as_posix(),
        "simulation_only": True,
        "drive_modes": {
            "default": "diff",
            "holonomic": "holonomic",
            "command_topic_in_source": "cmd_vel",
        },
        "lidar": {
            "sensor_name": "laser_sensor",
            "type": "ray",
            "update_rate_hz": block_value(lidar_block, "update_rate", float),
            "horizontal_samples": block_value(lidar_block, "samples", int),
            "min_angle_rad": block_value(lidar_block, "min_angle", float),
            "max_angle_rad": block_value(lidar_block, "max_angle", float),
            "range_min_m": block_value(lidar_block, "min", float),
            "range_max_m": block_value(lidar_block, "max", float),
            "noise_stddev_m": block_value(lidar_block, "stddev", float),
            "frame": block_value(lidar_block, "frame_name", str),
        },
        "camera": {
            "sensor_name": "camera_sensor",
            "type": "rgb",
            "update_rate_hz": block_value(camera_block, "update_rate", float),
            "width_px": block_value(camera_block, "width", int),
            "height_px": block_value(camera_block, "height", int),
            "horizontal_fov_rad": block_value(camera_block, "horizontal_fov", float),
            "near_m": block_value(camera_block, "near", float),
            "far_m": block_value(camera_block, "far", float),
            "frame": block_value(camera_block, "frame_name", str),
        },
        "depth_camera": {
            "sensor_name": "depth_sensor",
            "type": "depth",
            "update_rate_hz": block_value(depth_block, "update_rate", float),
            "width_px": block_value(depth_block, "width", int),
            "height_px": block_value(depth_block, "height", int),
            "near_m": block_value(depth_block, "near", float),
            "far_m": block_value(depth_block, "far", float),
            "frame": block_value(depth_block, "frame_name", str),
        },
        "imu": {
            "sensor_name": "imu_sensor",
            "type": "imu",
            "update_rate_hz": block_value(imu_block, "update_rate", float),
            "frame": block_value(imu_block, "frame_name", str),
        },
    }


def planar_footprint(
    meshes: dict[str, Any],
    link_origins: dict[str, dict[str, list[float]]],
) -> dict[str, Any]:
    mesh_names = {
        "base_link": "base_link.STL",
        "controller_link": "controller_link.STL",
        "lf_wheel_link": "lf_wheel_link.STL",
        "lb_wheel_link": "lb_wheel_link.STL",
        "rf_wheel_link": "rf_wheel_link.STL",
        "rb_wheel_link": "rb_wheel_link.STL",
        "camera_link": "camera_link.STL",
        "laser_link": "laser.STL",
    }
    points: list[tuple[float, float, float]] = []
    for link, mesh_name in mesh_names.items():
        record = meshes[mesh_name]
        transform = link_origins.get(link, {"xyz_m": [0.0, 0.0, 0.0], "rpy_rad": [0.0, 0.0, 0.0]})
        tx, ty, tz = (float(value) for value in transform["xyz_m"])
        roll, pitch, yaw = (float(value) for value in transform["rpy_rad"])
        cr, sr = math.cos(roll), math.sin(roll)
        cp, sp = math.cos(pitch), math.sin(pitch)
        cy, sy = math.cos(yaw), math.sin(yaw)
        rotation = (
            (cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr),
            (sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr),
            (-sp, cp * sr, cp * cr),
        )
        for x in (record["min"][0], record["max"][0]):
            for y in (record["min"][1], record["max"][1]):
                for z in (record["min"][2], record["max"][2]):
                    local = (float(x), float(y), float(z))
                    points.append(
                        tuple(
                            sum(rotation[row][column] * local[column] for column in range(3))
                            + (tx, ty, tz)[row]
                            for row in range(3)
                        )
                    )
    minimum = [min(point[index] for point in points) for index in range(3)]
    maximum = [max(point[index] for point in points) for index in range(3)]
    half_extents = [max(abs(minimum[index]), abs(maximum[index])) for index in range(2)]
    return {
        "method": "circumscribed_xy_radius_of_urdf_mesh_bounds_and_fixed_mounts",
        "bounds_m": {"min": minimum, "max": maximum},
        "half_extents_m": half_extents,
        "footprint_radius_m": math.hypot(*half_extents),
        "physical_validation": "pending_target_unit_measurement",
    }


def robot_spec() -> dict[str, Any]:
    root = ElementTree.parse(URDF).getroot()
    package_root = ElementTree.parse(PACKAGE_XML).getroot()
    wheel_links = {
        "fl": "lf_wheel_link",
        "fr": "rf_wheel_link",
        "rl": "lb_wheel_link",
        "rr": "rb_wheel_link",
    }
    wheel_origins: dict[str, list[float]] = {}
    wheel_joints: dict[str, dict[str, Any]] = {}
    fixed_origins: dict[str, dict[str, list[float]]] = {}
    link_origins: dict[str, dict[str, list[float]]] = {}
    link_meshes: dict[str, dict[str, list[str]]] = {}
    link_masses: dict[str, float] = {}
    total_mass = 0.0
    for link in root.findall("link"):
        link_name = link.attrib.get("name", "")
        link_meshes[link_name] = {"visual": [], "collision": []}
        for section in ("visual", "collision"):
            for mesh in link.findall(f"{section}/geometry/mesh"):
                filename = mesh.attrib.get("filename")
                if filename:
                    link_meshes[link_name][section].append(filename)
        mass = link.find("inertial/mass")
        if mass is not None:
            link_mass = float(mass.attrib["value"])
            link_masses[link_name] = link_mass
            total_mass += link_mass
    for joint in root.findall("joint"):
        name = joint.attrib.get("name", "")
        origin = joint.find("origin")
        if origin is None:
            continue
        xyz = parse_xyz(origin.attrib.get("xyz"))
        rpy = parse_rpy(origin.attrib.get("rpy"))
        child = joint.find("child")
        child_name = child.attrib.get("link", "") if child is not None else ""
        if child_name:
            link_origins[child_name] = {"xyz_m": xyz, "rpy_rad": rpy}
        key = next((item for item, link in wheel_links.items() if link == child_name), None)
        if key is not None:
            wheel_origins[key] = xyz
            axis = joint.find("axis")
            wheel_joints[key] = {
                "joint": name,
                "type": joint.attrib.get("type", ""),
                "axis": parse_xyz(axis.attrib.get("xyz")) if axis is not None else None,
                "origin_m": xyz,
                "link": child_name,
            }
        if name in {"camera_joint", "laser_joint"}:
            fixed_origins[name] = {"xyz_m": xyz, "rpy_rad": rpy}
    if set(wheel_origins) != set(wheel_links):
        raise ValueError("mini_mec_robot.urdf does not expose all four wheel joints")
    xs = [value[0] for value in wheel_origins.values()]
    ys = [value[1] for value in wheel_origins.values()]
    half_length = (max(xs) - min(xs)) / 2.0
    half_width = (max(ys) - min(ys)) / 2.0
    match = re.search(r'<xacro:wheel name="lf"[^>]*>', XACRO.read_text(encoding="utf-8"))
    radius_match = re.search(r'<geometry><cylinder radius="([0-9.eE+-]+)"', XACRO.read_text(encoding="utf-8"))
    if match is None or radius_match is None:
        raise ValueError("mini_mec_gazebo.urdf.xacro does not expose the wheel radius")
    wheel_radius = float(radius_match.group(1))
    if not all(value > 0.0 and math.isfinite(value) for value in (wheel_radius, half_length, half_width)):
        raise ValueError("derived mini-Mecanum geometry is invalid")
    wheel_components = {
        key: {
            **wheel_joints[key],
            "mass_kg": link_masses.get(wheel_links[key]),
            "mesh": link_meshes[wheel_links[key]],
        }
        for key in ("fl", "fr", "rl", "rr")
    }
    sensor_components = {
        "camera": {
            "hardware_target": "Astra-S",
            "urdf_link": "camera_link",
            "urdf_joint": "camera_joint",
            "mount": fixed_origins.get("camera_joint"),
            "mesh": link_meshes.get("camera_link"),
            "status": "mount_defined; calibration_and_device_identity_pending",
        },
        "lidar": {
            "hardware_target": "N10P",
            "urdf_link": "laser_link",
            "urdf_joint": "laser_joint",
            "mount": fixed_origins.get("laser_joint"),
            "mesh": link_meshes.get("laser_link"),
            "status": "mount_defined; baudrate_and_device_identity_pending",
        },
        "imu": {
            "hardware_target": "STM32 telemetry IMU",
            "urdf_link": "base_link",
            "status": "source_xacro_only; hardware_channel_pending",
        },
    }
    mesh_records = mesh_inventory()
    return {
        "model": "mini_mec_robot",
        "urdf_package": {
            "name": package_root.findtext("name"),
            "version": package_root.findtext("version"),
            "description": " ".join((package_root.findtext("description") or "").split()),
            "license": package_root.findtext("license"),
            "package_xml_sha256": sha256(PACKAGE_XML),
            "cmake_sha256": sha256(PACKAGE_CMAKE),
            "install_directories": ["meshes", "rviz", "urdf"],
            "available_urdf_models": sorted(path.stem for path in (URDF_PACKAGE / "urdf").glob("*.urdf")),
            "urdf_catalog": urdf_catalog(),
        },
        "urdf": URDF.relative_to(ROOT).as_posix(),
        "urdf_sha256": sha256(URDF),
        "xacro": XACRO.relative_to(ROOT).as_posix(),
        "xacro_sha256": sha256(XACRO),
        "mass_kg_from_urdf": total_mass,
        "link_meshes": link_meshes,
        "wheel_radius_m": wheel_radius,
        "half_length_m": half_length,
        "half_width_m": half_width,
        "wheel_origins_m": wheel_origins,
        "components": {
            "wheels": wheel_components,
            "sensors": sensor_components,
            "link_masses_kg": link_masses,
        },
        "camera_joint": fixed_origins.get("camera_joint"),
        "laser_joint": fixed_origins.get("laser_joint"),
        "xacro_sensor_contract": xacro_sensor_contract(),
        "footprint": planar_footprint(mesh_records["mini_mec_robot"], link_origins),
        "mesh_inventory": mesh_records,
        "state_definition": STATE,
        "control_interface": "body_velocity",
        "stm32": {
            "device": "/dev/rai_controller",
            "baudrate": 115200,
            "command_bytes": 11,
            "telemetry_bytes": 24,
            "header": "0x7B",
            "tail": "0x7D",
            "checksum": "xor",
            "quantization": "1e-3 SI units",
        },
        "n10p": {
            "profile": PROFILE,
            "baudrate": "must be measured on the supplied unit",
            "packet_bytes": 108,
        },
        "middleware_source": {
            "bridge_cpp": (REFERENCE_ROOT / "turn_on_rai_robot" / "src" / "rai_robot.cpp").relative_to(ROOT).as_posix(),
            "bridge_header": (REFERENCE_ROOT / "turn_on_rai_robot" / "include" / "turn_on_rai_robot" / "rai_robot.h").relative_to(ROOT).as_posix(),
            "serial_launch": (REFERENCE_ROOT / "turn_on_rai_robot" / "launch" / "base_serial.launch.py").relative_to(ROOT).as_posix(),
            "udev_rules": {
                "path": UDEV.relative_to(ROOT).as_posix(),
                "sha256": sha256(UDEV),
            },
        },
    }


def ports() -> list[dict[str, str]]:
    try:
        from serial.tools import list_ports
    except ImportError:
        return []
    return [
        {
            "device": str(item.device),
            "description": str(item.description or ""),
            "vid": "" if item.vid is None else f"0x{item.vid:04x}",
            "pid": "" if item.pid is None else f"0x{item.pid:04x}",
            "serial_number": str(item.serial_number or ""),
        }
        for item in list_ports.comports()
    ]


def inspect(args: argparse.Namespace) -> int:
    report = {
        "schema": "cca-hardware-intake-v1",
        "created_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "robot": robot_spec(),
        "serial_ports": ports(),
        "runtime": {
            "python": sys.version.split()[0],
            "openni2_importable": (
                _importable("openni2")
                or _importable("openni.openni2")
                or _importable("primesense.openni2")
            ),
            "pyserial_importable": _importable("serial"),
            "ultralytics_importable": _importable("ultralytics"),
        },
        "status": "device_candidates_found" if ports() else "no_serial_device_detected",
    }
    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


def _importable(name: str) -> bool:
    try:
        __import__(name)
    except Exception:
        return False
    return True


def measured_geometry(path: Path | None) -> tuple[dict[str, Any], str | None]:
    if path is None:
        return {
            "wheel_radius_m": None,
            "half_length_m": None,
            "half_width_m": None,
            "sensor_mounts": None,
            "footprint": {
                "method": "pending_physical_measurement",
                "footprint_radius_m": None,
                "physical_validation": "pending_target_unit_measurement",
            },
            "wheel_signs": {"fl": 1, "fr": 1, "rl": 1, "rr": 1},
            "geometry_authority": "pending_physical_measurement",
        }, None
    if not path.is_file():
        raise FileNotFoundError(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"physical geometry file is not valid JSON: {path}") from error
    if payload.get("schema") != "cca-physical-robot-v1":
        raise ValueError("physical geometry file must use schema cca-physical-robot-v1")
    if payload.get("status") != "measured":
        raise ValueError("physical geometry file must be status=measured")
    if payload.get("robot_model") != "mini_mec_robot":
        raise ValueError("physical geometry file must identify mini_mec_robot")
    values = [payload.get(name) for name in ("wheel_radius_m", "half_length_m", "half_width_m", "footprint_radius_m")]
    if not all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) and float(value) > 0.0 for value in values):
        raise ValueError("measured physical geometry values must be positive finite numbers")
    signs_payload = payload.get("wheel_signs")
    names = ("fl", "fr", "rl", "rr")
    if not isinstance(signs_payload, dict) or any(
        name not in signs_payload
        or isinstance(signs_payload[name], bool)
        or not isinstance(signs_payload[name], int)
        or signs_payload[name] not in (-1, 1)
        for name in names
    ):
        raise ValueError("physical wheel_signs must explicitly contain fl/fr/rl/rr as -1 or 1")
    signs = {name: int(signs_payload[name]) for name in names}
    mounts_payload = payload.get("sensor_mounts")
    sensor_mounts = None
    if mounts_payload is not None:
        required_mounts = (
            "lidar_height_m",
            "camera_height_m",
            "lidar_front_edge_distance_m",
            "camera_front_edge_distance_m",
            "lidar_position_x_m",
            "camera_position_x_m",
            "camera_pitch_deg",
            "camera_pitch_rad",
            "pitch_direction",
        )
        if not isinstance(mounts_payload, dict) or any(name not in mounts_payload for name in required_mounts):
            raise ValueError("sensor_mounts must contain lidar/camera heights and camera pitch")
        numeric_mounts = {name: mounts_payload[name] for name in required_mounts[:-1]}
        if not all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
            for value in numeric_mounts.values()
        ):
            raise ValueError("sensor mount values must be finite numbers")
        if any(float(mounts_payload[name]) <= 0.0 for name in ("lidar_height_m", "camera_height_m")):
            raise ValueError("sensor heights must be positive")
        if any(float(mounts_payload[name]) < 0.0 for name in ("lidar_front_edge_distance_m", "camera_front_edge_distance_m")):
            raise ValueError("sensor front-edge distances must be non-negative")
        expected_lidar_x = float(values[1]) - float(mounts_payload["lidar_front_edge_distance_m"])
        expected_camera_x = float(values[1]) - float(mounts_payload["camera_front_edge_distance_m"])
        if not math.isclose(expected_lidar_x, float(mounts_payload["lidar_position_x_m"]), rel_tol=0.0, abs_tol=1.0e-6) or not math.isclose(
            expected_camera_x, float(mounts_payload["camera_position_x_m"]), rel_tol=0.0, abs_tol=1.0e-6
        ):
            raise ValueError("sensor front-edge offsets and robot-frame positions disagree")
        if mounts_payload["pitch_direction"] not in {"downward", "upward", "level"}:
            raise ValueError("sensor pitch_direction is invalid")
        if not math.isclose(
            math.radians(float(mounts_payload["camera_pitch_deg"])),
            float(mounts_payload["camera_pitch_rad"]),
            rel_tol=0.0,
            abs_tol=1.0e-6,
        ):
            raise ValueError("camera pitch degrees and radians disagree")
        sensor_mounts = {
            name: float(mounts_payload[name])
            for name in required_mounts[:-1]
        }
        sensor_mounts["pitch_direction"] = str(mounts_payload["pitch_direction"])
    return {
        "wheel_radius_m": float(values[0]),
        "half_length_m": float(values[1]),
        "half_width_m": float(values[2]),
        "footprint": {
            "method": "measured_physical_spec",
            "footprint_radius_m": float(values[3]),
            "physical_validation": "measured_target_unit",
        },
        "wheel_signs": signs,
        "sensor_mounts": sensor_mounts,
        "geometry_authority": "measured_physical_spec",
    }, sha256(path)


def prepare(args: argparse.Namespace) -> int:
    spec = robot_spec()
    geometry, physical_spec_sha256 = measured_geometry(getattr(args, "physical_spec", None))
    output = args.output.resolve()
    if not args.stm_port.strip() or not args.lidar_port.strip():
        raise ValueError("--stm-port and --lidar-port are required")
    if args.lidar_baud <= 0:
        raise ValueError("--lidar-baud must be positive")
    if not args.firmware.strip():
        raise ValueError("--firmware must identify the STM32 firmware")
    config = {
        "schema": "cca-hardware-runtime-v1",
        "transport": "stm32_serial",
        "stm32": {
            "port": args.stm_port,
            "baudrate": 115200,
            "timeout_s": 0.1,
            "mode": 0,
        },
        "camera": {
            "model": "Astra-S",
            "sdk": "OpenNI2",
            "uri": args.camera_uri,
            "sdk_path": args.sdk_path,
            "depth_scale_m": 0.001,
            "max_pair_skew_us": args.max_pair_skew_us,
        },
        "lidar": {
            "model": "N10P",
            "port": args.lidar_port,
            "baudrate": args.lidar_baud,
            "protocol_profile": PROFILE,
            "timeout_s": 0.1,
        },
        "can": {"interface": "socketcan", "channel": None, "bitrate": 500000},
        "firmware": args.firmware,
        "clock": args.clock,
        "control_mode": "position_state",
        "state_definition": STATE,
        "urdf_path": None,
        "urdf_source": "mini_mec_robot",
        "physical_spec_path": args.physical_spec.resolve().as_posix() if args.physical_spec else None,
        "wheel_radius_m": geometry["wheel_radius_m"],
        "half_length_m": geometry["half_length_m"],
        "half_width_m": geometry["half_width_m"],
        "footprint": geometry["footprint"],
        "wheel_signs": geometry["wheel_signs"],
        "sensor_mounts": geometry["sensor_mounts"],
        "geometry_authority": geometry["geometry_authority"],
        "source": {
            "urdf_sha256": spec["urdf_sha256"],
            "xacro_sha256": spec["xacro_sha256"],
            "physical_spec_sha256": physical_spec_sha256,
            "derived_from": "URDF/xacro are protocol and mount references only; physical geometry is measured separately",
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"config": output.as_posix(), "robot": spec}, indent=2, ensure_ascii=False))
    return 0


def schedule(args: argparse.Namespace) -> int:
    if args.speed_mps <= 0.0 or args.duration_s <= 0.0 or args.step_s <= 0.0:
        raise ValueError("speed, duration and step must be positive")
    rows: list[tuple[float, float, float, float]] = []
    count = max(1, int(math.ceil(args.duration_s / args.step_s)))
    for index in range(count):
        t = min(index * args.step_s, args.duration_s)
        phase = index % 4 if args.kind == "square" else 0
        if args.kind == "forward" or (args.kind == "square" and phase == 0):
            command = (args.speed_mps, 0.0, 0.0)
        elif args.kind == "lateral" or (args.kind == "square" and phase == 1):
            command = (0.0, args.speed_mps, 0.0)
        elif args.kind == "rotate" or (args.kind == "square" and phase == 2):
            command = (0.0, 0.0, args.angular_radps)
        else:
            command = (-args.speed_mps, 0.0, 0.0)
        rows.append((t, *command))
    rows.append((args.duration_s, 0.0, 0.0, 0.0))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("t_s", "vx_mps", "vy_mps", "wz_radps"))
        writer.writerows(rows)
    print(json.dumps({"schedule": args.output.as_posix(), "rows": len(rows), "kind": args.kind}, indent=2))
    return 0


def _capture_preflight(args: argparse.Namespace) -> dict[str, Any]:
    from ai.detection import validate_engine_manifest
    from hardware import RobotGeometry
    from shared import validate_capture_calibration
    from tools.final_pack import read_map
    from tools.record_hardware import (
        CONTEXT_DT_S,
        load_command_schedule,
        load_controller_map,
        load_object,
        validate_config,
        validate_robot_source,
    )

    config_path = args.config.resolve()
    calibration_path = args.calibration.resolve()
    map_path = args.map_path.resolve()
    engine_path = args.pose_engine.resolve()
    pose_manifest_path = args.pose_manifest.resolve()
    output_path = args.output.resolve()
    frames_path = (
        args.frames_root.resolve()
        if args.frames_root is not None
        else output_path.parent / f"{output_path.name}-frames"
    )
    if output_path.exists() and (not output_path.is_dir() or any(output_path.iterdir())):
        raise ValueError(f"output directory must be absent or empty: {output_path}")
    if frames_path.exists() and (not frames_path.is_dir() or any(frames_path.iterdir())):
        raise ValueError(f"frames directory must be absent or empty: {frames_path}")
    config = load_object(config_path)
    validate_config(config)
    geometry = RobotGeometry.from_json(config_path)
    source_hashes = validate_robot_source(config, config_path)
    calibration = load_object(calibration_path)
    validate_capture_calibration(calibration, camera="Astra-S", lidar="N10P")
    map_payload = read_map(map_path)
    engine_manifest = validate_engine_manifest(engine_path, pose_manifest_path)
    if args.duration_s <= 0.0 or args.sample_period_s <= 0.0:
        raise ValueError("duration and sample period must be positive")
    if abs(float(args.sample_period_s) - CONTEXT_DT_S) > 1.0e-9:
        raise ValueError(f"sample period must equal the frozen context contract ({CONTEXT_DT_S:g} s)")
    transport = str(config.get("transport", "cca_can"))
    schedule_rows = 1
    if args.controller == "cca_nmpc":
        if transport != "stm32_serial":
            raise ValueError("online CCA requires transport=stm32_serial")
        if not args.confirm_motion:
            raise ValueError("CCA-NMPC motion requires --confirm-motion after H0 approval")
        if args.command_csv is not None:
            raise ValueError("online CCA cannot be combined with --command-csv")
        if args.lstm_checkpoint is None or not args.lstm_checkpoint.is_file():
            raise ValueError("online CCA requires an existing --lstm-checkpoint")
        load_controller_map(map_path)
    elif args.command_csv is not None:
        if not args.confirm_motion:
            raise ValueError("scheduled motion requires --confirm-motion after H0 approval")
        if transport != "stm32_serial":
            raise ValueError("scheduled motion requires transport=stm32_serial")
        schedule_rows = len(load_command_schedule(args.command_csv.resolve()))
    motion_requested = bool(args.confirm_motion and (args.controller == "cca_nmpc" or args.command_csv is not None))
    safety_record = None
    if motion_requested:
        safety_path = getattr(args, "safety_record", None)
        if safety_path is None:
            raise ValueError("motion requires --safety-record with H0 stop checks")
        from tools.record_hardware import validate_safety_record

        safety_path = safety_path.resolve()
        validate_safety_record(safety_path)
        safety_record = {"path": safety_path.as_posix(), "sha256": sha256(safety_path)}
    if args.lstm_checkpoint is not None and not args.lstm_checkpoint.is_file():
        raise FileNotFoundError(args.lstm_checkpoint)
    return {
        "schema": "cca-hardware-preflight-v1",
        "status": "PASS",
        "devices_opened": False,
        "motion_requested": motion_requested,
        "controller": args.controller,
        "transport": transport,
        "duration_s": float(args.duration_s),
        "sample_period_s": float(args.sample_period_s),
        "schedule_rows": schedule_rows,
        "robot": {
            "model": config.get("urdf_source"),
            "wheel_radius_m": geometry.wheel_radius_m,
            "half_length_m": geometry.half_length_m,
            "half_width_m": geometry.half_width_m,
            "sensor_mounts": config.get("sensor_mounts"),
            "source": source_hashes,
            "footprint_radius_m": config["footprint"]["footprint_radius_m"],
        },
        "map": {"path": map_path.as_posix(), "frame_id": str(map_payload["frame_id"])},
        "calibration": {"path": calibration_path.as_posix(), "calibration_id": calibration["calibration_id"]},
        "pose_engine": {
            "path": engine_path.as_posix(),
            "sha256": str(engine_manifest["engineSha256"]),
            "model": str(engine_manifest["model"]),
        },
        "lstm_checkpoint": args.lstm_checkpoint.resolve().as_posix() if args.lstm_checkpoint else None,
        "safety_record": safety_record,
        "output": output_path.as_posix(),
        "frames_root": frames_path.as_posix(),
    }


def preflight(args: argparse.Namespace) -> int:
    report = _capture_preflight(args)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")
    return 0


def record(args: argparse.Namespace) -> int:
    _capture_preflight(args)
    if args.controller == "cca_nmpc" and not args.confirm_motion:
        raise ValueError("CCA-NMPC motion requires --confirm-motion after H0 approval")
    if args.command_csv is not None and not args.confirm_motion:
        raise ValueError("scheduled motion requires --confirm-motion after H0 approval")
    from tools.record_hardware import run as record_run

    forwarded = argparse.Namespace(
        config=args.config,
        calibration=args.calibration,
        map_path=args.map_path,
        pose_engine=args.pose_engine,
        pose_manifest=args.pose_manifest,
        lstm_checkpoint=args.lstm_checkpoint,
        output=args.output,
        frames_root=args.frames_root,
        duration_s=args.duration_s,
        sample_period_s=args.sample_period_s,
        controller=args.controller,
        command_csv=args.command_csv,
        allow_actuation=args.confirm_motion,
        safety_record=getattr(args, "safety_record", None),
    )
    return record_run(forwarded)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="No-ROS mini-Mecanum hardware entrypoint")
    sub = root.add_subparsers(dest="command", required=True)
    inspect_parser = sub.add_parser("inspect")
    inspect_parser.add_argument("--output", type=Path)
    inspect_parser.set_defaults(handler=inspect)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--output", type=Path, required=True)
    prepare_parser.add_argument("--stm-port", required=True)
    prepare_parser.add_argument("--lidar-port", required=True)
    prepare_parser.add_argument("--lidar-baud", type=int, required=True)
    prepare_parser.add_argument("--firmware", required=True)
    prepare_parser.add_argument("--camera-uri")
    prepare_parser.add_argument("--sdk-path")
    prepare_parser.add_argument("--max-pair-skew-us", type=float)
    prepare_parser.add_argument("--physical-spec", type=Path)
    prepare_parser.add_argument("--clock", choices=("system_time", "robot_time"), default="system_time")
    prepare_parser.set_defaults(handler=prepare)
    schedule_parser = sub.add_parser("schedule")
    schedule_parser.add_argument("--output", type=Path, required=True)
    schedule_parser.add_argument("--kind", choices=("forward", "lateral", "rotate", "square"), required=True)
    schedule_parser.add_argument("--duration-s", type=float, required=True)
    schedule_parser.add_argument("--step-s", type=float, default=0.1)
    schedule_parser.add_argument("--speed-mps", type=float, default=0.05)
    schedule_parser.add_argument("--angular-radps", type=float, default=0.2)
    schedule_parser.set_defaults(handler=schedule)
    preflight_parser = sub.add_parser("preflight")
    preflight_parser.add_argument("--config", type=Path, required=True)
    preflight_parser.add_argument("--calibration", type=Path, required=True)
    preflight_parser.add_argument("--map", dest="map_path", type=Path, required=True)
    preflight_parser.add_argument("--pose-engine", type=Path, required=True)
    preflight_parser.add_argument("--pose-manifest", type=Path, required=True)
    preflight_parser.add_argument("--lstm-checkpoint", type=Path)
    preflight_parser.add_argument("--output", type=Path, required=True)
    preflight_parser.add_argument("--frames-root", type=Path)
    preflight_parser.add_argument("--duration-s", type=float, required=True)
    preflight_parser.add_argument("--sample-period-s", type=float, default=0.1)
    preflight_parser.add_argument("--controller", choices=("external", "cca_nmpc"), default="external")
    preflight_parser.add_argument("--command-csv", type=Path)
    preflight_parser.add_argument("--confirm-motion", action="store_true")
    preflight_parser.add_argument("--safety-record", type=Path)
    preflight_parser.add_argument("--report", type=Path)
    preflight_parser.set_defaults(handler=preflight)
    record_parser = sub.add_parser("record")
    record_parser.add_argument("--config", type=Path, required=True)
    record_parser.add_argument("--calibration", type=Path, required=True)
    record_parser.add_argument("--map", dest="map_path", type=Path, required=True)
    record_parser.add_argument("--pose-engine", type=Path, required=True)
    record_parser.add_argument("--pose-manifest", type=Path, required=True)
    record_parser.add_argument("--lstm-checkpoint", type=Path)
    record_parser.add_argument("--output", type=Path, required=True)
    record_parser.add_argument("--frames-root", type=Path)
    record_parser.add_argument("--duration-s", type=float, required=True)
    record_parser.add_argument("--sample-period-s", type=float, default=0.1)
    record_parser.add_argument("--controller", choices=("external", "cca_nmpc"), default="external")
    record_parser.add_argument("--command-csv", type=Path)
    record_parser.add_argument("--confirm-motion", action="store_true")
    record_parser.add_argument("--safety-record", type=Path)
    record_parser.set_defaults(handler=record)
    return root


def main() -> int:
    args = parser().parse_args()
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
