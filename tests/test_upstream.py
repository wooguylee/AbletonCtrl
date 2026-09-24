import ast
import asyncio
import importlib.util
import inspect
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = json.loads((ROOT / "doc/upstream-tools.json").read_text(encoding="utf-8"))


class UpstreamParityTests(unittest.IsolatedAsyncioTestCase):
    def test_vendored_sources_match_pinned_hashes(self):
        manifest = json.loads((ROOT / "doc/upstream-source.json").read_text())
        for entry in manifest["files"]:
            self.assertEqual(hashlib.sha256((ROOT / entry["local_path"]).read_bytes()).hexdigest(), entry["sha256"])

    async def test_every_upstream_tool_and_parameter_is_preserved(self):
        self.assertIsNotNone(importlib.util.find_spec("ableton_arrangement_mcp.compatibility"),
                             "Combined upstream compatibility layer is missing")
        from ableton_arrangement_mcp.server import create_server
        from ableton_arrangement_mcp.upstream import server as upstream
        class Connection:
            def call(self, method, params=None):
                return {}
        server = create_server(Connection())
        tools = {t.name: t for t in await server.list_tools()}
        originals = {t.name: t for t in await upstream.mcp.list_tools()}
        expected = {t["name"] for t in INVENTORY["tools"]}
        self.assertEqual(set(originals), expected)
        for name in expected:
            self.assertIn(name, tools)
            self.assertEqual(tools[name].inputSchema, originals[name].inputSchema, name)
        self.assertIn("ableton_create_arrangement_midi_clip", tools)
        self.assertTrue("ableton_move_arrangement_clip" in tools, "Arrangement move tool is missing")

    async def test_preserved_tool_uses_authenticated_bridge_command(self):
        self.assertIsNotNone(importlib.util.find_spec("ableton_arrangement_mcp.compatibility"))
        from ableton_arrangement_mcp.server import create_server
        class Connection:
            def __init__(self):
                self.calls = []
            def call(self, method, params=None):
                self.calls.append((method, params))
                if method == "upstream.get_script_info":
                    return {"script_version": "1.7.1", "capabilities": ["get_clip_notes"]}
                return {"tempo": 128, "tracks": []}
        client = Connection()
        server = create_server(client)
        result = await server.call_tool("get_session_info", {})
        self.assertIn("upstream.get_session_info", [name for name, _ in client.calls])
        self.assertIn("128", str(result))


if __name__ == "__main__":
    unittest.main()
