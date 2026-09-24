import importlib.util
import json
import socket
import threading
import time
import unittest
from fakes import make_api

TOKEN = "test-token-" + "a" * 40


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("remote_script.AbletonArrangementMCP.transport"),
                             "TCP transport has not been implemented")
        from remote_script.AbletonArrangementMCP.transport import JSONTCPBridge
        self.api, self.song = make_api()
        self.bridge = JSONTCPBridge(self.api.call, TOKEN, port=0)
        self.port = self.bridge.port
        self.stop = threading.Event()
        def pump():
            while not self.stop.is_set():
                self.bridge.poll()
                self.stop.wait(0.002)
        self.worker = threading.Thread(target=pump)
        self.worker.start()

    def tearDown(self):
        if hasattr(self, "stop"):
            self.stop.set()
            self.worker.join(2)
            self.bridge.close()

    def request(self, **overrides):
        req = {"id": "test", "token": TOKEN, "deadline": time.time() + 5,
               "method": "status", "params": {}}
        req.update(overrides)
        return req

    def raw(self, payload, fragmented=False):
        with socket.create_connection(("127.0.0.1", self.port), 2) as sock:
            if fragmented:
                sock.sendall(payload[:7])
                time.sleep(0.01)
                sock.sendall(payload[7:])
            else:
                sock.sendall(payload)
            data = b""
            while not data.endswith(b"\n"):
                chunk = sock.recv(65536)
                if not chunk:
                    break
                data += chunk
            return json.loads(data)

    def test_fragmented_frame_roundtrip(self):
        reply = self.raw((json.dumps(self.request()) + "\n").encode(), True)
        self.assertEqual(reply["id"], "test")
        self.assertEqual(reply["result"]["live_version"], "12.fake")

    def test_auth_expiry_and_unknown_method(self):
        for params, code in [({"token": "wrong"}, "UNAUTHORIZED"),
                             ({"deadline": time.time() - 1}, "EXPIRED"),
                             ({"method": "eval"}, "UNKNOWN_METHOD")]:
            reply = self.raw((json.dumps(self.request(**params)) + "\n").encode())
            self.assertEqual(reply["error"]["code"], code)
        self.assertEqual(self.song.undo_count, 0)

    def test_malformed_frame_does_not_kill_server(self):
        reply = self.raw(b"broken json\n")
        self.assertEqual(reply["error"]["code"], "INVALID_REQUEST")
        self.assertIn("result", self.raw((json.dumps(self.request()) + "\n").encode()))

    def test_reused_request_id_is_not_executed_again(self):
        track_id = self.api.call("list_tracks", {})["tracks"][0]["track_id"]
        payload = (json.dumps(self.request(method="create_midi_clip", params={
            "track_id": track_id, "start_beats": 4, "length_beats": 4})) + "\n").encode()
        self.assertIn("result", self.raw(payload))
        self.assertEqual(self.raw(payload)["error"]["code"], "DUPLICATE_REQUEST")
        self.assertEqual(self.song.undo_count, 1)

    def test_client_and_remote_error(self):
        from ableton_arrangement_mcp.client import BridgeClient, BridgeClientError
        client = BridgeClient(TOKEN, self.port, timeout=2)
        self.assertEqual(client.call("status")["tempo"], 120.0)
        with self.assertRaisesRegex(BridgeClientError, "STALE_HANDLE"):
            client.call("get_clip", {"clip_id": "missing"})

    def test_client_timeout_has_no_retry(self):
        from ableton_arrangement_mcp.client import BridgeClient, BridgeClientError
        self.stop.set()
        self.worker.join(2)
        track_id = self.api.call("list_tracks", {})["tracks"][0]["track_id"]
        with self.assertRaisesRegex(BridgeClientError, "outcome is unknown"):
            BridgeClient(TOKEN, self.port, timeout=0.1).call("create_midi_clip", {
                "track_id": track_id, "start_beats": 4, "length_beats": 4})
        time.sleep(0.05)
        for _ in range(5):
            self.bridge.poll()
        self.assertEqual(self.song.undo_count, 0)

    def test_oversized_frame_is_disconnected(self):
        from remote_script.AbletonArrangementMCP.transport import MAX_FRAME
        with socket.create_connection(("127.0.0.1", self.port), 2) as sock:
            sock.sendall(b"x" * (MAX_FRAME + 1))
            self.assertEqual(sock.recv(1), b"")
        self.assertEqual(self.song.undo_count, 0)

    def test_deferred_response_completes_on_later_polls_same_thread(self):
        from remote_script.AbletonArrangementMCP.deferred import Deferred
        owners = []
        def action():
            owners.append(threading.get_ident())
            yield
            owners.append(threading.get_ident())
            return {'completed': True}
        self.bridge.handler = lambda *_: Deferred(action()).advance()
        reply = self.raw((json.dumps(self.request()) + '\n').encode())
        self.assertEqual(reply['result'], {'completed': True})
        self.assertEqual(owners, [self.worker.ident, self.worker.ident])

    def test_close_cancels_pending_action_and_runs_cleanup(self):
        from remote_script.AbletonArrangementMCP.deferred import Deferred
        self.stop.set()
        self.worker.join(2)
        cleaned = []
        def action():
            try:
                while True:
                    yield
            finally:
                cleaned.append(True)
        self.bridge.handler = lambda *_: Deferred(action()).advance()
        with socket.create_connection(('127.0.0.1', self.port), 2) as sock:
            sock.sendall((json.dumps(self.request())+'\n').encode())
            self.bridge.poll()
            self.assertEqual(cleaned, [])
            self.bridge.close()
        self.assertEqual(cleaned, [True])


if __name__ == "__main__":
    unittest.main()
