import io
import json
from types import SimpleNamespace

from app.backend.robot_console import Peer, RobotService, ZERO


def test_legacy_tcp_accepts_repeated_commands_and_manual_stop():
    robot = RobotService("127.0.0.1", 0)
    writes = []
    events = []
    robot.stm = SimpleNamespace(send_velocity=lambda *values: writes.append(values))
    robot.status_payload = lambda: {}
    robot.load_saved_map = lambda: None
    commands = [
        {"command": "arm", "enabled": True},
        {"command": "velocity", "vx": .1},
        {"command": "velocity", "vx": .2},
        {"command": "velocity"},
        {"command": "velocity", "vy": .1},
    ]
    stream = io.BytesIO("".join(json.dumps(command) + "\n" for command in commands).encode())

    class TestPeer:
        sock = SimpleNamespace(settimeout=lambda timeout: None, makefile=lambda mode: stream)

        def enqueue(self, payload):
            events.append(payload)

        def close(self):
            pass

    peer = TestPeer()
    robot.peers.add(peer)
    robot._client_loop(peer)
    assert robot.armed and robot.last_command == (0.0, .1, 0.0)
    assert writes == [(.1, 0.0, 0.0), (.2, 0.0, 0.0), ZERO, (0.0, .1, 0.0)]
    assert all(event.get("event") != "error" for event in events)
    robot.handle(peer, {"command": "emergency_stop"})
    assert not robot.armed and writes[-1] == ZERO


def test_control_precedes_streams_and_latest_frames_do_not_starve_map():
    peer = Peer(SimpleNamespace(), "test")
    for message_type in ("state", "map", "pose", "state", "event"):
        peer.enqueue({"type": message_type})

    assert json.loads(peer._next_packet())["type"] == "event"
    assert json.loads(peer._next_packet())["type"] == "state"
    peer.enqueue({"type": "state"})
    assert json.loads(peer._next_packet())["type"] == "map"
    assert json.loads(peer._next_packet())["type"] == "pose"


def test_fusion_queue_replaces_waiting_scan():
    robot = RobotService("127.0.0.1", 0)
    assert robot._enqueue_map_fusion(("older", None, None, None))
    assert robot._enqueue_map_fusion(("latest", None, None, None))
    assert robot.map_fusion_queue.get_nowait().scan == "latest"
    robot.map_fusion_queue.task_done()
    assert robot.map_fusion_queue.unfinished_tasks == 0
    assert robot.map_scans_dropped == 1
