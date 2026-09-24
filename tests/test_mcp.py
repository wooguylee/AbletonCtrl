import importlib.util
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from fakes import make_api


class MCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_stdio_discovery_and_clip_lifecycle(self):
        self.assertIsNotNone(importlib.util.find_spec("ableton_arrangement_mcp.server"),
                             "MCP server has not been implemented")
        from remote_script.AbletonArrangementMCP.transport import JSONTCPBridge
        api, song = make_api()
        token = "mcp-test-" + "b" * 40
        bridge = JSONTCPBridge(api.call, token, port=0)
        stop = threading.Event()
        def pump():
            while not stop.is_set():
                bridge.poll()
                stop.wait(0.002)
        worker = threading.Thread(target=pump)
        worker.start()
        try:
            with tempfile.TemporaryDirectory() as directory:
                config = Path(directory) / "config.json"
                config.write_text(json.dumps({"token": token, "port": bridge.port}), encoding="utf-8")
                params = StdioServerParameters(command=sys.executable,
                    args=["-m", "ableton_arrangement_mcp", "--config", str(config)], cwd=directory)
                async with stdio_client(params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        listing = await session.list_tools()
                        self.assertEqual(len(listing.tools), 10)
                        tools = {t.name: t for t in listing.tools}
                        self.assertTrue(tools["ableton_status"].annotations.readOnlyHint)
                        self.assertTrue(tools["ableton_delete_arrangement_clip"].annotations.destructiveHint)
                        async def call(name, arguments=None):
                            response = await session.call_tool(name, arguments or {})
                            self.assertFalse(response.isError, response.content)
                            return response.structuredContent
                        self.assertEqual((await call("ableton_status"))["live_version"], "12.fake")
                        track = (await call("ableton_list_tracks"))["tracks"][0]["track_id"]
                        created = await call("ableton_create_arrangement_midi_clip", {"track_id": track, "start_beats": 4, "length_beats": 4})
                        clip = created["clip_id"]
                        updated = await call("ableton_update_arrangement_clip", {"clip_id": clip, "name": "MCP 테스트", "muted": True})
                        self.assertEqual(updated["name"], "MCP 테스트")
                        await call("ableton_add_midi_notes", {"clip_id": clip, "notes": [{"pitch": 60, "start_time": 0, "duration": 1}]})
                        notes = await call("ableton_get_midi_notes", {"clip_id": clip})
                        self.assertEqual(notes["notes"][0]["pitch"], 60)
                        copied = await call("ableton_duplicate_arrangement_clip", {"clip_id": clip, "destination_beats": 8})
                        await call("ableton_delete_arrangement_clip", {"clip_id": copied["clip_id"]})
                        stale = await session.call_tool("ableton_get_arrangement_clip", {"clip_id": copied["clip_id"]})
                        self.assertTrue(stale.isError)
                        invalid = await session.call_tool("ableton_add_midi_notes", {"clip_id": clip, "notes": [{"pitch": 128, "start_time": 0, "duration": 1}]})
                        self.assertTrue(invalid.isError)
                        bad_bool = await session.call_tool("ableton_create_arrangement_midi_clip", {"track_id": track, "start_beats": True, "length_beats": 4})
                        self.assertTrue(bad_bool.isError)
                        self.assertEqual(song.undo_depth, 0)
        finally:
            stop.set()
            worker.join(2)
            bridge.close()


if __name__ == "__main__":
    unittest.main()
