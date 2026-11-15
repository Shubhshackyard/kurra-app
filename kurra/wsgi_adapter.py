"""Single-Threaded ASGI to WSGI Bridge for PythonAnywhere & uWSGI environments.

Runs the ASGI application in the current thread using an event loop,
avoiding uWSGI GIL deadlocks caused by background threading in a2wsgi.
"""
from __future__ import annotations
import asyncio
from io import BytesIO
from typing import Any, Callable, Dict, List, Tuple


class SingleThreadASGItoWSGI:
    def __init__(self, asgi_app: Any):
        self.asgi_app = asgi_app

    def __call__(self, environ: Dict[str, Any], start_response: Callable) -> List[bytes]:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._handle(environ, start_response))
        finally:
            loop.close()

    async def _handle(self, environ: Dict[str, Any], start_response: Callable) -> List[bytes]:
        path = environ.get("PATH_INFO", "")
        query_string = environ.get("QUERY_STRING", "").encode("latin1")
        method = environ.get("REQUEST_METHOD", "GET")
        headers: List[Tuple[bytes, bytes]] = []

        for k, v in environ.items():
            if k.startswith("HTTP_"):
                headers.append((k[5:].lower().replace("_", "-").encode("latin1"), str(v).encode("latin1")))
            elif k in ("CONTENT_TYPE", "CONTENT_LENGTH"):
                headers.append((k.lower().replace("_", "-").encode("latin1"), str(v).encode("latin1")))

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method,
            "path": path,
            "raw_path": path.encode("latin1"),
            "query_string": query_string,
            "headers": headers,
            "server": (environ.get("SERVER_NAME", "localhost"), int(environ.get("SERVER_PORT", 80))),
        }

        body_io = environ.get("wsgi.input")
        content_length = int(environ.get("CONTENT_LENGTH") or 0)
        body_bytes = body_io.read(content_length) if body_io and content_length > 0 else (body_io.read() if body_io else b"")

        response_status = 200
        response_headers: List[Tuple[str, str]] = []
        response_body: List[bytes] = []

        async def receive() -> Dict[str, Any]:
            return {
                "type": "http.request",
                "body": body_bytes,
                "more_body": False
            }

        async def send(message: Dict[str, Any]) -> None:
            nonlocal response_status, response_headers, response_body
            if message["type"] == "http.response.start":
                response_status = message["status"]
                response_headers = [(k.decode("latin1"), v.decode("latin1")) for k, v in message.get("headers", [])]
            elif message["type"] == "http.response.body":
                response_body.append(message.get("body", b""))

        await self.asgi_app(scope, receive, send)

        status_str = f"{response_status} OK" if response_status == 200 else f"{response_status} Response"
        start_response(status_str, response_headers)
        return response_body
