from __future__ import annotations

import asyncio
import os
import threading
import time
from typing import Any

import rclpy
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from starlette.middleware.gzip import GZipMiddleware

from .node import WebBridgeNode


app = FastAPI(title="CCA-NMPC HTTP Runtime Bridge", version="0.1.0")
app.add_middleware(GZipMiddleware, minimum_size=1024, compresslevel=1)
control_node: WebBridgeNode | None = None
spin_thread: threading.Thread | None = None
peer_connections: set[Any] = set()

DEVICE_ROLE = os.getenv("RAI_DEVICE_ROLE", "robot").strip().lower() or "robot"
DEVICE_LABEL = os.getenv("RAI_DEVICE_LABEL", "cca_robot").strip() or "cca_robot"
BRIDGE_HOST = os.getenv("RAI_BRIDGE_HOST", "0.0.0.0")
BRIDGE_PORT = int(os.getenv("RAI_BRIDGE_PORT", "8000"))
ALLOWED_ACTIONS = [
    "camera",
    "hardware",
    "lidar",
    "navigation",
    "slam",
    "system",
]


class VelocityCommand(BaseModel):
    linear_x: float = Field(default=0.0, ge=-1.5, le=1.5)
    linear_y: float = Field(default=0.0, ge=-1.5, le=1.5)
    angular_z: float = Field(default=0.0, ge=-3.0, le=3.0)


class NavGoal(BaseModel):
    x: float
    y: float
    yaw: float = 0.0


class MapSaveRequest(BaseModel):
    name: str | None = Field(default=None, max_length=128)


class InitialPose(BaseModel):
    x: float
    y: float
    yaw: float = 0.0


def _require_node() -> WebBridgeNode:
    if control_node is None or not rclpy.ok():
        raise HTTPException(status_code=503, detail="ROS runtime bridge is not ready")
    return control_node


def _system_components(node: WebBridgeNode) -> dict[str, Any]:
    node.ensure_telemetry_subscriptions()
    return {
        "device_role": DEVICE_ROLE,
        "device_label": DEVICE_LABEL,
        "allowed_actions": ALLOWED_ACTIONS,
        "bridge_host": BRIDGE_HOST,
        "bridge_port": BRIDGE_PORT,
        "operation_mode": "real",
        "components": node.component_states(),
        "mapping": node.mapping_status(),
    }


@app.get("/health")
@app.get("/api/health")
async def health() -> dict[str, Any]:
    node = _require_node()
    return {
        "status": "ok",
        "bridge": "online",
        "ros": rclpy.ok(),
        "device_role": DEVICE_ROLE,
        "device_label": DEVICE_LABEL,
        "components": len(node.component_states()),
    }


@app.get("/api/system/runtime")
async def runtime() -> dict[str, Any]:
    node = _require_node()
    return {
        "status": "running",
        "device_role": DEVICE_ROLE,
        "device_label": DEVICE_LABEL,
        "ros_domain_id": os.getenv("ROS_DOMAIN_ID", "0"),
        "rmw_implementation": os.getenv("RMW_IMPLEMENTATION", ""),
        "components": node.component_states(),
        "mapping": node.mapping_status(),
    }


@app.get("/api/system/components")
async def components() -> dict[str, Any]:
    return _system_components(_require_node())


@app.get("/api/telemetry/current")
async def telemetry_current() -> dict[str, Any]:
    node = _require_node()
    node.ensure_telemetry_subscriptions()
    return {"timestamp": time.time(), "telemetry": node.telemetry_snapshot()}


@app.get("/api/map/snapshot")
async def map_snapshot() -> dict[str, Any]:
    node = _require_node()
    node.ensure_map_subscription()
    deadline = time.monotonic() + 1.5
    snapshot = node.map_snapshot()
    while snapshot is None and time.monotonic() < deadline:
        await asyncio.sleep(0.05)
        snapshot = node.map_snapshot()
    return {"available": snapshot is not None, "map": snapshot}


def _map_operation_error(error: Exception) -> HTTPException:
    status_code = 400 if isinstance(error, ValueError) else 503
    return HTTPException(status_code=status_code, detail=str(error))


def _navigation_operation_error(error: Exception) -> HTTPException:
    if isinstance(error, ValueError):
        status_code = 400
    elif isinstance(error, RuntimeError):
        status_code = 409
    else:
        status_code = 503
    return HTTPException(status_code=status_code, detail=str(error))


@app.get("/api/map/status")
async def mapping_status() -> dict[str, Any]:
    node = _require_node()
    node.ensure_map_subscription()
    return node.mapping_status()


@app.post("/api/map/scan/start")
async def mapping_start() -> dict[str, Any]:
    try:
        return _require_node().set_mapping_enabled(True)
    except Exception as error:
        raise _map_operation_error(error) from error


@app.post("/api/map/scan/stop")
async def mapping_stop() -> dict[str, Any]:
    try:
        return _require_node().set_mapping_enabled(False)
    except Exception as error:
        raise _map_operation_error(error) from error


@app.post("/api/map/select")
async def mapping_select(request: MapSaveRequest) -> dict[str, Any]:
    try:
        return _require_node().select_map(request.name)
    except Exception as error:
        raise _map_operation_error(error) from error


@app.post("/api/map/localization/pose")
async def localization_pose(request: InitialPose) -> dict[str, Any]:
    try:
        return _require_node().set_initial_pose(request.x, request.y, request.yaw)
    except Exception as error:
        raise _navigation_operation_error(error) from error


@app.post("/api/map/clear")
async def mapping_clear() -> dict[str, Any]:
    try:
        return _require_node().clear_map()
    except Exception as error:
        raise _map_operation_error(error) from error


@app.post("/api/map/save")
async def mapping_save(request: MapSaveRequest) -> dict[str, Any]:
    try:
        return _require_node().save_map(request.name)
    except Exception as error:
        raise _map_operation_error(error) from error


@app.post("/api/robot/cmd_vel")
async def command_velocity(command: VelocityCommand) -> dict[str, Any]:
    node = _require_node()
    node.publish_cmd_vel(command.linear_x, command.linear_y, command.angular_z)
    return {
        "accepted": True,
        "command": {
            "linear_x": command.linear_x,
            "linear_y": command.linear_y,
            "angular_z": command.angular_z,
        },
        "timestamp": time.time(),
    }


@app.post("/api/robot/nav/goal")
async def navigation_goal(goal: NavGoal) -> dict[str, Any]:
    try:
        node = _require_node()
        return node.send_nav_goal(goal.x, goal.y, goal.yaw)
    except Exception as error:
        raise _navigation_operation_error(error) from error


@app.post("/api/robot/nav/cancel")
async def navigation_cancel() -> dict[str, Any]:
    return _require_node().cancel_navigation()


async def _close_peer(peer: Any, track: Any) -> None:
    peer_connections.discard(peer)
    try:
        track.stop()
    except Exception:
        pass
    try:
        await peer.close()
    except Exception:
        pass


@app.post("/api/webrtc/offer")
async def webrtc_offer(offer: dict[str, Any]) -> dict[str, str]:
    node = _require_node()
    offer_type = str(offer.get("type", ""))
    offer_sdp = offer.get("sdp")
    if offer_type != "offer" or not isinstance(offer_sdp, str) or not offer_sdp:
        raise HTTPException(status_code=400, detail="A WebRTC offer with type and sdp is required")

    try:
        from aiortc import RTCPeerConnection, RTCSessionDescription
        from .webrtc import RosImageVideoTrack
    except ImportError as error:
        raise HTTPException(
            status_code=503,
            detail="WebRTC dependencies are not installed on the robot",
        ) from error

    peer = RTCPeerConnection()
    track = RosImageVideoTrack(node)
    peer_connections.add(peer)
    node.register_camera_client()
    peer.addTrack(track)

    @peer.on("connectionstatechange")
    async def on_connection_state_change() -> None:
        if peer.connectionState in {"failed", "closed", "disconnected"}:
            await _close_peer(peer, track)

    try:
        await peer.setRemoteDescription(
            RTCSessionDescription(sdp=offer_sdp, type=offer_type)
        )
        answer = await peer.createAnswer()
        await peer.setLocalDescription(answer)
        if peer.localDescription is None:
            raise RuntimeError("WebRTC answer was not created")
        return {
            "type": peer.localDescription.type,
            "sdp": peer.localDescription.sdp,
        }
    except Exception as error:
        await _close_peer(peer, track)
        raise HTTPException(status_code=502, detail=f"WebRTC negotiation failed: {error}") from error


def main() -> None:
    global control_node, spin_thread
    rclpy.init(args=None)
    control_node = WebBridgeNode()
    spin_thread = threading.Thread(
        target=rclpy.spin,
        args=(control_node,),
        name="cca-bridge-ros-spin",
        daemon=True,
    )
    spin_thread.start()
    try:
        uvicorn.run(app, host=BRIDGE_HOST, port=BRIDGE_PORT, log_level="info")
    finally:
        for peer in tuple(peer_connections):
            try:
                asyncio.run(peer.close())
            except Exception:
                pass
        if control_node is not None:
            control_node.destroy_node()
            control_node = None
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
