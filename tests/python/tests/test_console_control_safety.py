import io
import json
from types import SimpleNamespace

from app.backend.robot_console import RobotService, ZERO


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

    class Peer:
        sock = SimpleNamespace(settimeout=lambda timeout: None, makefile=lambda mode: stream)

        def enqueue(self, payload):
            events.append(payload)

        def close(self):
            pass

    peer = Peer()
    robot.peers.add(peer)
    robot._client_loop(peer)
    assert robot.armed and robot.last_command == (0.0, .1, 0.0)
    assert writes == [(.1, 0.0, 0.0), (.2, 0.0, 0.0), ZERO, (0.0, .1, 0.0)]
    assert all(event.get("event") != "error" for event in events)
    robot.handle(peer, {"command": "emergency_stop"})
    assert not robot.armed and writes[-1] == ZERO
