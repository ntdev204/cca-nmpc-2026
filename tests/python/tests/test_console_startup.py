import asyncio
import socket
from concurrent.futures import TimeoutError as FutureTimeoutError
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import struct
import threading
import time

import pytest

from app.backend import robot_console as console


@pytest.mark.parametrize("failure", [ConnectionResetError, ConnectionAbortedError, BrokenPipeError])
def test_expected_client_disconnect_ends_only_connection(failure):
    handler = console.CameraMjpegHandler.__new__(console.CameraMjpegHandler)
    for method in ("handle", "finish"):
        with patch.object(BaseHTTPRequestHandler, method, side_effect=failure()):
            getattr(handler, method)()
            assert handler.close_connection


def test_real_http_reset_does_not_break_camera_server():
    class TestHandler(console.CameraMjpegHandler):
        def do_GET(self):
            self._send_json(200, {"ready": True})

    failures = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), TestHandler)
    server.daemon_threads = True
    server.handle_error = lambda *args: failures.append(args)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        for _ in range(3):
            with socket.create_connection(server.server_address) as client:
                client.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
                assert b"200 OK" in client.recv(4096)
                client.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
        time.sleep(.05)
        with socket.create_connection(server.server_address) as client:
            client.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n")
            response = b""
            while part := client.recv(4096):
                response += part
            assert b'"ready":true' in response
        assert failures == []
    finally:
        server.shutdown()
        server.server_close()
        worker.join(1)


def test_unexpected_handler_errors_are_not_silenced():
    handler = console.CameraMjpegHandler.__new__(console.CameraMjpegHandler)
    with patch.object(BaseHTTPRequestHandler, "handle", side_effect=ValueError("bug")):
        with pytest.raises(ValueError, match="bug"):
            handler.handle()


def test_broken_openni_exception_can_be_reported():
    class BrokenError(Exception):
        def __str__(self):
            raise AttributeError("OniStatus.val")
    assert console.error_text(BrokenError()) == "BrokenError"


def test_duplicate_console_never_opens_hardware():
    with socket.socket() as owner:
        owner.bind(("127.0.0.1", 0))
        owner.listen(1)
        service = console.RobotService("127.0.0.1", owner.getsockname()[1])
        with patch.object(service, "start_sources") as sources:
            service.serve()
        sources.assert_not_called()
        assert service.server_socket is None


def test_timed_out_offer_is_cancelled():
    service = console.RobotService("127.0.0.1", 0)
    service.webrtc_loop = object()
    class Future:
        cancelled = False
        def result(self, timeout):
            raise FutureTimeoutError()
        def cancel(self):
            self.cancelled = True
    future = Future()
    def schedule(coro, loop):
        coro.close()
        return future
    with patch.object(console, "WEBRTC_AVAILABLE", True), patch.object(console.asyncio, "run_coroutine_threadsafe", schedule):
        with pytest.raises(TimeoutError, match="negotiation timed out"):
            service.create_webrtc_answer({"type": "offer", "sdp": "test"})
    assert future.cancelled


def test_concurrent_offers_are_serialized():
    service = console.RobotService("127.0.0.1", 0)
    active = peak = 0
    async def negotiate(sdp, offer_type):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(.01)
        active -= 1
        return {"sdp": sdp}
    service._create_webrtc_answer_locked = negotiate
    async def run():
        await asyncio.gather(service._create_webrtc_answer("one", "offer"),
                             service._create_webrtc_answer("two", "offer"))
    asyncio.run(run())
    assert peak == 1
