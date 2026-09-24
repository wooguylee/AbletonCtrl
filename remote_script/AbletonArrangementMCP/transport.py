"""Bounded nonblocking TCP transport. poll() must run on Live's main thread."""
import hmac
import json
import math
import socket
import time
from collections import OrderedDict
from .api import BridgeError
from .deferred import Deferred

MAX_FRAME = 16 * 1024 * 1024
MAX_CLIENTS = 8
CHUNK_SIZE = 256 * 1024
IDLE_SECONDS = 15


def reject_constant(value):
    raise ValueError("Non-finite JSON number")


class JSONTCPBridge:
    def __init__(self, handler, token, port=8765):
        if not isinstance(token, str) or len(token) < 32 or not token.isascii():
            raise ValueError("Configure an ASCII token of at least 32 characters")
        self.handler = handler
        self.token = token
        self.clients = {}
        self.seen = OrderedDict()
        self.pending = None
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Intentionally no SO_REUSEADDR on Windows: another process must not hijack the port.
            self.listener.bind(("127.0.0.1", port))
            self.listener.listen(MAX_CLIENTS)
            self.listener.setblocking(False)
        except Exception:
            self.listener.close()
            raise
        self.port = self.listener.getsockname()[1]

    def _drop(self, sock):
        self.clients.pop(sock, None)
        sock.close()

    def _dispatch(self, frame):
        request_id = None
        try:
            req = json.loads(frame.decode("utf-8"), parse_constant=reject_constant)
            if not isinstance(req, dict):
                raise ValueError("Request must be an object")
            request_id = req.get("id")
            if not isinstance(request_id, str) or not 1 <= len(request_id) <= 128:
                request_id = None
                raise ValueError("id must be a string of 1 to 128 characters")
            token = req.get("token")
            if not isinstance(token, str) or not token.isascii() or not hmac.compare_digest(token, self.token):
                raise BridgeError("UNAUTHORIZED", "Bridge token does not match")
            deadline = req.get("deadline")
            now = time.time()
            if type(deadline) not in (int, float) or not math.isfinite(deadline):
                raise ValueError("A finite Unix deadline is required")
            if deadline <= now:
                raise BridgeError("EXPIRED", "Request expired before Live execution; no operation performed")
            if deadline > now + IDLE_SECONDS:
                raise ValueError("deadline may be at most 15 seconds in the future")
            if not isinstance(req.get("method"), str) or not isinstance(req.get("params", {}), dict):
                raise ValueError("method must be a string and params an object")
            if request_id in self.seen:
                raise BridgeError("DUPLICATE_REQUEST", "Request ID already processed; do not replay writes")
            self.seen[request_id] = True
            if len(self.seen) > 2048:
                self.seen.popitem(last=False)
            result = self.handler(req["method"], req.get("params", {}))
            if isinstance(result, Deferred):
                return (request_id, result)
            response = {"id": request_id, "result": result}
        except BridgeError as exc:
            response = {"id": request_id, "error": {"code": exc.code, "message": str(exc)}}
        except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
            response = {"id": request_id, "error": {"code": "INVALID_REQUEST", "message": str(exc)}}
        except Exception:
            response = {"id": request_id, "error": {"code": "INTERNAL_ERROR", "message": "Bridge failed; a write outcome may be unknown"}}
        return self._encode(response)

    @staticmethod
    def _encode(response):
        try:
            encoded = json.dumps(response, ensure_ascii=True, allow_nan=False).encode("utf-8") + b"\n"
            if len(encoded) <= MAX_FRAME:
                return encoded
        except (ValueError, TypeError):
            pass
        return (json.dumps({"id": response.get("id"), "error": {"code": "RESPONSE_TOO_LARGE",
                           "message": "Response unavailable; inspect state before retrying any write"}}) + "\n").encode()

    def poll(self):
        # A continuation runs once per update, on this same Live thread. Do not
        # interleave other MCP commands with a staged edit or an open Undo step.
        if self.pending is not None:
            sock, state, request_id, action, started = self.pending
            try:
                if time.monotonic() - started > IDLE_SECONDS:
                    action.close()
                    raise BridgeError("TIMEOUT", "Live update did not finish in time; inspect the Set before retrying")
                result = action.advance()
                if isinstance(result, Deferred):
                    return
                response = {"id": request_id, "result": result}
            except BridgeError as exc:
                response = {"id": request_id, "error": {"code": exc.code, "message": str(exc)}}
            except Exception as exc:
                response = {"id": request_id, "error": {"code": "LIVE_ERROR", "message": "%s; inspect the Set before retrying" % exc}}
            state["output"] = self._encode(response)
            state["since"] = time.monotonic()
            self.pending = None
        for _ in range(MAX_CLIENTS):
            try:
                sock, _ = self.listener.accept()
            except (BlockingIOError, OSError):
                break
            if len(self.clients) >= MAX_CLIENTS:
                sock.close()
                continue
            sock.setblocking(False)
            self.clients[sock] = {"input": bytearray(), "output": None, "since": time.monotonic()}
        for sock, state in list(self.clients.items()):
            if time.monotonic() - state["since"] > IDLE_SECONDS:
                self._drop(sock)
                continue
            try:
                if state["output"] is None:
                    try:
                        data = sock.recv(CHUNK_SIZE)
                    except BlockingIOError:
                        continue
                    if not data:
                        self._drop(sock)
                        continue
                    state["input"].extend(data)
                    if len(state["input"]) > MAX_FRAME:
                        self._drop(sock)
                        continue
                    if b"\n" not in state["input"]:
                        continue
                    frame, _, trailing = bytes(state["input"]).partition(b"\n")
                    if trailing.strip():
                        state["output"] = b'{"id":null,"error":{"code":"INVALID_REQUEST","message":"One request per connection"}}\n'
                    else:
                        state["output"] = self._dispatch(frame)
                        if isinstance(state["output"], tuple):
                            request_id, action = state["output"]
                            state["output"] = None
                            self.pending = (sock, state, request_id, action, time.monotonic())
                            return
                    state["since"] = time.monotonic()  # Long native calls get a fresh response-send window.
                try:
                    sent = sock.send(state["output"][:CHUNK_SIZE])
                except BlockingIOError:
                    continue
                state["output"] = state["output"][sent:]
                if not state["output"]:
                    self._drop(sock)
            except OSError:
                self._drop(sock)

    def close(self):
        if self.pending is not None:
            action = self.pending[3]
            self.pending = None
            try:
                action.close()
            except Exception:
                pass  # Still close sockets if Live is already tearing down a Set.
        for sock in list(self.clients):
            self._drop(sock)
        self.listener.close()
