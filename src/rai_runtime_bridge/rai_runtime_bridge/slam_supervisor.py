from __future__ import annotations

import os
import shutil
import signal
import subprocess
import threading
from typing import Any

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


class SlamSupervisor(Node):
    """Own exactly one SLAM launch session and expose safe start/stop/reset calls."""

    def __init__(self) -> None:
        super().__init__("slam_session_manager")
        self.slam_package = str(
            self.declare_parameter("slam_package", "cca_slam").value
        )
        self.slam_launch_file = str(
            self.declare_parameter(
                "slam_launch_file", "online_async_launch.py"
            ).value
        )
        self.slam_params_file = str(
            self.declare_parameter("slam_params_file", "").value
        )
        # rclpy declares use_sim_time on Node automatically when launch passes
        # the standard parameter override, so do not declare it a second time.
        self.use_sim_time = _as_bool(self.get_parameter("use_sim_time").value)
        self.start_on_launch = _as_bool(
            self.declare_parameter("start_on_launch", True).value
        )
        self.ros2_executable = str(
            self.declare_parameter("ros2_executable", "").value
        ) or shutil.which("ros2") or "/opt/ros/humble/bin/ros2"
        self.start_service = str(
            self.declare_parameter("start_service", "/slam_manager/start").value
        )
        self.stop_service = str(
            self.declare_parameter("stop_service", "/slam_manager/stop").value
        )
        self.reset_service = str(
            self.declare_parameter("reset_service", "/slam_manager/reset").value
        )

        self._lock = threading.RLock()
        self._launch_process: subprocess.Popen[Any] | None = None
        self._startup_timer = None
        self.create_service(Trigger, self.start_service, self._start_callback)
        self.create_service(Trigger, self.stop_service, self._stop_callback)
        self.create_service(Trigger, self.reset_service, self._reset_callback)

        if self.start_on_launch:
            # Let the sensor launch publish the static laser TF and establish
            # the first scan stream before SLAM creates its message filter.
            # Starting both actions at the same instant can fill that filter
            # before `laser` is transformable and leave mapping stuck.
            self._startup_timer = self.create_timer(
                2.0, self._start_after_sensor_warmup
            )

    def _start_after_sensor_warmup(self) -> None:
        timer = self._startup_timer
        self._startup_timer = None
        if timer is not None:
            timer.cancel()
            self.destroy_timer(timer)
        started, message = self._start_process()
        if started:
            self.get_logger().info(message)
        else:
            self.get_logger().error(message)

    def _launch_command(self) -> list[str]:
        command = [
            self.ros2_executable,
            "launch",
            self.slam_package,
            self.slam_launch_file,
            f"use_sim_time:={'true' if self.use_sim_time else 'false'}",
        ]
        if self.slam_params_file:
            command.append(f"slam_params_file:={self.slam_params_file}")
        return command

    def _is_running(self) -> bool:
        return (
            self._launch_process is not None
            and self._launch_process.poll() is None
        )

    def _cancel_startup_timer(self) -> None:
        timer = self._startup_timer
        self._startup_timer = None
        if timer is not None:
            timer.cancel()
            self.destroy_timer(timer)

    def _start_process(self) -> tuple[bool, str]:
        with self._lock:
            if self._is_running():
                return True, "SLAM launch is already running."
            try:
                self._launch_process = subprocess.Popen(
                    self._launch_command(),
                    start_new_session=True,
                )
            except OSError as error:
                self._launch_process = None
                return False, f"Could not start SLAM launch: {error}"
            return True, f"SLAM launch started (pid={self._launch_process.pid})."

    def _stop_process(self) -> tuple[bool, str]:
        with self._lock:
            self._cancel_startup_timer()
            process = self._launch_process
            if process is None or process.poll() is not None:
                self._launch_process = None
                return True, "SLAM launch is already stopped."

            try:
                os.killpg(process.pid, signal.SIGINT)
            except ProcessLookupError:
                self._launch_process = None
                return True, "SLAM launch already exited."

            try:
                process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                    process.wait(timeout=2.0)
                except (ProcessLookupError, subprocess.TimeoutExpired):
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    try:
                        process.wait(timeout=1.0)
                    except subprocess.TimeoutExpired:
                        return False, "SLAM launch did not stop in time."
            finally:
                self._launch_process = None
            return True, "SLAM launch stopped."

    def _reset_process(self) -> tuple[bool, str]:
        stopped, stop_message = self._stop_process()
        if not stopped:
            return False, stop_message
        started, start_message = self._start_process()
        return started, f"{stop_message} {start_message}"

    def _start_callback(
        self, request: Trigger.Request, response: Trigger.Response
    ) -> Trigger.Response:
        del request
        response.success, response.message = self._start_process()
        return response

    def _stop_callback(
        self, request: Trigger.Request, response: Trigger.Response
    ) -> Trigger.Response:
        del request
        response.success, response.message = self._stop_process()
        return response

    def _reset_callback(
        self, request: Trigger.Request, response: Trigger.Response
    ) -> Trigger.Response:
        del request
        response.success, response.message = self._reset_process()
        return response

    def destroy_node(self) -> bool:
        self._stop_process()
        return super().destroy_node()


def main() -> None:
    rclpy.init(args=None)
    node = SlamSupervisor()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
