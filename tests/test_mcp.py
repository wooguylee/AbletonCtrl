import importlib.util
import json
import sys
import tempfile
import threading
import unittest
import types
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from fakes import make_api
from test_surface import surface_module


class MCPTests(unittest.IsolatedAsyncioTestCase):
    async def test_stdio_discovery_and_clip_lifecycle(self):
        self.assertIsNotNone(importlib.util.find_spec("ableton_arrangement_mcp.server"),
                             "MCP server has not been implemented")
        from remote_script.AbletonArrangementMCP.transport import JSONTCPBridge
        api, song = make_api()
        token = "mcp-test-" + "b" * 40
        surface = surface_module().ArrangementSurface.__new__(surface_module().ArrangementSurface)
        surface._song, surface._api = song, api
        surface._dispatching_upstream = surface._capture_passive = False
        surface.context = types.SimpleNamespace(song=song)
        surface.scheduled = []
        bridge = JSONTCPBridge(surface.dispatch, token, port=0)
        surface._bridge = bridge
        stop = threading.Event()
        def pump():
            surface._owner_thread = threading.get_ident()
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
                        self.assertEqual(len(listing.tools), 54)
                        tools = {t.name: t for t in listing.tools}
                        self.assertTrue(tools["ableton_status"].annotations.readOnlyHint)
                        self.assertTrue(tools["ableton_delete_arrangement_clip"].annotations.destructiveHint)
                        async def call(name, arguments=None):
                            response = await session.call_tool(name, arguments or {})
                            self.assertFalse(response.isError, response.content)
                            return response.structuredContent
                        async def legacy(name, arguments=None):
                            result = (await call(name, arguments))["result"]
                            self.assertNotIn("error", result.lower(), result)
                            return result
                        self.assertEqual(json.loads(await legacy("get_session_info"))["tempo"], 120)
                        await legacy("set_tempo", {"tempo": 130})
                        self.assertEqual(song.tempo, 130)
                        await legacy("create_midi_track")
                        await legacy("create_audio_track")
                        self.assertEqual(len(song.tracks), 4)
                        await legacy("set_track_name", {"track_index": 0, "name": "Original MCP"})
                        await legacy("create_clip", {"track_index": 0, "clip_index": 0, "length": 4})
                        await legacy("set_clip_name", {"track_index": 0, "clip_index": 0, "name": "Session notes"})
                        await legacy("add_notes_to_clip", {"track_index": 0, "clip_index": 0, "notes": [{"pitch": 64, "start_time": 0, "duration": 1}]})
                        self.assertEqual(json.loads(await legacy("get_clip_notes", {"track_index": 0, "clip_index": 0}))["note_count"], 1)
                        await legacy("fire_clip", {"track_index": 0, "clip_index": 0})
                        self.assertTrue(song.tracks[0].clip_slots[0].clip.is_playing)
                        await legacy("stop_clip", {"track_index": 0, "clip_index": 0})
                        await legacy("get_track_info", {"track_index": 0})
                        await legacy("get_device_parameters", {"track_index": 0, "device_index": 0})
                        await legacy("set_device_parameter", {"track_index": 0, "device_index": 0, "parameter_index": 0, "value": 0.7})
                        self.assertEqual(song.tracks[0].devices[0].parameters[0].value, 0.7)
                        await legacy("start_playback")
                        self.assertTrue(song.is_playing)
                        await legacy("stop_playback")
                        await legacy("set_arrangement_time", {"time": 8})
                        await legacy("get_arrangement_clips", {"track_index": 0})
                        await legacy("get_session_snapshot", {"include_notes": True, "include_params": True})
                        await legacy("delete_clip", {"track_index": 0, "clip_index": 0})
                        self.assertFalse(song.tracks[0].clip_slots[0].has_clip)
                        self.assertEqual((await call("ableton_status"))["live_version"], "12.fake")
                        track = (await call("ableton_list_tracks"))["tracks"][0]["track_id"]
                        created = await call("ableton_create_arrangement_midi_clip", {"track_id": track, "start_beats": 4, "length_beats": 4})
                        clip = created["clip_id"]
                        updated = await call("ableton_update_arrangement_clip", {"clip_id": clip, "name": "MCP 테스트", "muted": True})
                        self.assertEqual(updated["name"], "MCP 테스트")
                        await call("ableton_add_midi_notes", {"clip_id": clip, "notes": [{"pitch": 60, "start_time": 0, "duration": 1}]})
                        notes = await call("ableton_get_midi_notes", {"clip_id": clip})
                        self.assertEqual(notes["notes"][0]["pitch"], 60)
                        note_id = notes["notes"][0]["note_id"]
                        await call("ableton_update_midi_notes", {"clip_id": clip, "notes": [{"note_id": note_id, "pitch": 67}]})
                        self.assertEqual((await call("ableton_get_midi_notes", {"clip_id": clip}))["notes"][0]["pitch"], 67)
                        await call("ableton_delete_midi_notes", {"clip_id": clip, "note_ids": [note_id]})
                        copied = await call("ableton_duplicate_arrangement_clip", {"clip_id": clip, "destination_beats": 8})
                        await call("ableton_delete_arrangement_clip", {"clip_id": copied["clip_id"]})
                        moved = await call("ableton_move_arrangement_clip", {"clip_id": clip, "destination_beats": 12})
                        clip = moved["clip_id"]
                        self.assertEqual(moved["start_beats"], 12)
                        trimmed = await call("ableton_trim_arrangement_clip", {"clip_id": clip, "start_beats": 13, "end_beats": 15})
                        clip = trimmed["clips"][0]["clip_id"]
                        resized = await call("ableton_resize_arrangement_clip", {"clip_id": clip, "start_beats": 12, "end_beats": 18})
                        clip = resized["clips"][0]["clip_id"]
                        self.assertEqual(resized["clips"][0]["end_beats"], 18)
                        target = (await call("ableton_list_tracks"))["tracks"][2]["track_id"]
                        cross_copy = await call("ableton_copy_arrangement_clip", {"clip_id": clip, "target_track_id": target, "destination_beats": 8})
                        self.assertEqual(cross_copy["track_id"], target)
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
