from __future__ import annotations

import asyncio
from fractions import Fraction
import time

import numpy as np
from aiortc import MediaStreamTrack
from aiortc.mediastreams import MediaStreamError
from av import VideoFrame

from .node import WebBridgeNode


class RosImageVideoTrack(MediaStreamTrack):
    """Convert ROS sensor_msgs/Image frames into a WebRTC video track."""

    kind = "video"
    target_fps = 15.0

    def __init__(self, node: WebBridgeNode) -> None:
        super().__init__()
        self._node = node
        self._sequence = 0
        self._stopped = False
        self._pts = 0
        self._last_emit_monotonic = 0.0

    async def recv(self) -> VideoFrame:
        if self._stopped:
            raise MediaStreamError
        now = time.monotonic()
        wait_s = (1.0 / self.target_fps) - (now - self._last_emit_monotonic)
        if wait_s > 0.0:
            await asyncio.sleep(wait_s)
        self._sequence, message = await asyncio.to_thread(
            self._node.wait_for_camera_frame, self._sequence
        )
        if message is None:
            raise MediaStreamError
        image = _image_to_bgr(message)
        frame = VideoFrame.from_ndarray(image, format="bgr24")
        self._pts += 3000
        frame.pts = self._pts
        frame.time_base = Fraction(1, 90000)
        self._last_emit_monotonic = time.monotonic()
        return frame

    def stop(self) -> None:
        if self._stopped:
            return
        self._stopped = True
        self._node.unregister_camera_client()
        super().stop()


def _image_to_bgr(message: object) -> np.ndarray:
    width = int(getattr(message, "width"))
    height = int(getattr(message, "height"))
    encoding = str(getattr(message, "encoding")).lower()
    step = int(getattr(message, "step"))
    raw = bytes(getattr(message, "data"))
    if width <= 0 or height <= 0 or step <= 0:
        raise MediaStreamError

    if encoding in {"bgr8", "rgb8", "bgra8", "rgba8"}:
        channels = 4 if len(encoding) == 5 else 3
        row_bytes = width * channels
        if step < row_bytes or len(raw) < step * height:
            raise MediaStreamError
        rows = np.frombuffer(raw, dtype=np.uint8).reshape(height, step)[:, :row_bytes]
        image = rows.reshape(height, width, channels)
        if encoding in {"rgb8", "rgba8"}:
            image = image[:, :, :3][:, :, ::-1]
        elif channels == 4:
            image = image[:, :, :3]
        return np.ascontiguousarray(image)

    if encoding in {"mono8", "8uc1"}:
        if step < width or len(raw) < step * height:
            raise MediaStreamError
        image = np.frombuffer(raw, dtype=np.uint8).reshape(height, step)[:, :width]
        return np.repeat(image[:, :, None], 3, axis=2)

    if encoding in {"mono16", "16uc1", "32fc1"}:
        dtype = np.float32 if encoding == "32fc1" else np.uint16
        item_size = np.dtype(dtype).itemsize
        row_bytes = width * item_size
        if step < row_bytes or len(raw) < step * height:
            raise MediaStreamError
        rows = np.frombuffer(raw, dtype=np.uint8).reshape(height, step)[:, :row_bytes]
        values = rows.copy().view(dtype).reshape(height, width).astype(np.float32)
        values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
        scale = 10.0 if encoding == "32fc1" else 4000.0
        image = np.clip(values / scale * 255.0, 0.0, 255.0).astype(np.uint8)
        return np.repeat(image[:, :, None], 3, axis=2)

    raise MediaStreamError
