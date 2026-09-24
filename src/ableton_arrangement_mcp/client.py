"""One-shot authenticated client. Never automatically retries a Live operation."""
import json
import math
import socket
import time
import uuid
from pathlib import Path

MAX_FRAME = 1024 * 1024


class BridgeClientError(RuntimeError):
    pass


class BridgeClient:
    def __init__(self, token: str, port: int = 8765, timeout: float = 10):
        if not isinstance(token, str) or len(token) < 32 or not token.isascii():
            raise ValueError("Configure an ASCII token of at least 32 characters")
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("Invalid bridge port")
        if type(timeout) not in (float, int) or not math.isfinite(timeout) or not 0 < timeout <= 15:
            raise ValueError("timeout must be greater than 0 and at most 15 seconds")
        self.token, self.port, self.timeout = token, port, timeout

    @classmethod
    def from_file(cls, path):
        config = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(config["token"], config.get("port", 8765), config.get("timeout", 10))

    def call(self, method: str, params: dict | None = None) -> dict:
        request_id = uuid.uuid4().hex
        request = {"id": request_id, "token": self.token, "method": method,
                   "params": params or {}, "deadline": time.time() + self.timeout * 0.8}
        payload = (json.dumps(request, allow_nan=False) + "\n").encode("utf-8")
        if len(payload) > MAX_FRAME:
            raise BridgeClientError("Request exceeds 1 MiB")
        until = time.monotonic() + self.timeout
        try:
            with socket.create_connection(("127.0.0.1", self.port), self.timeout) as sock:
                sock.settimeout(max(0.001, until - time.monotonic()))
                sock.sendall(payload)
                response = bytearray()
                while b"\n" not in response:
                    remaining = until - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError()
                    sock.settimeout(remaining)
                    part = sock.recv(65536)
                    if not part:
                        raise BridgeClientError("Bridge disconnected; write outcome is unknown. Inspect the Set before retrying.")
                    response.extend(part)
                    if len(response) > MAX_FRAME:
                        raise BridgeClientError("Bridge response exceeds 1 MiB; inspect state before retrying")
        except ConnectionRefusedError as exc:
            raise BridgeClientError("BRIDGE_UNAVAILABLE: Start Live and select AbletonArrangementMCP as a Control Surface") from exc
        except (OSError, TimeoutError) as exc:
            raise BridgeClientError("Bridge timeout/connection failure; write outcome is unknown. Do not retry automatically; inspect the Set.") from exc
        try:
            reply = json.loads(response.partition(b"\n")[0])
            if not isinstance(reply, dict) or reply.get("id") != request_id:
                raise ValueError("Response ID does not match")
            if "error" in reply:
                error = reply["error"]
                raise BridgeClientError("%s: %s" % (error["code"], error["message"]))
            if not isinstance(reply.get("result"), dict):
                raise ValueError("Missing result object")
            return reply["result"]
        except (ValueError, KeyError, TypeError) as exc:
            raise BridgeClientError("Invalid bridge reply; write outcome is unknown") from exc
