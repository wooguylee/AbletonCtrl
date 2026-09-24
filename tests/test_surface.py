import importlib
import json
import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import patch
from fakes import make_api


class FakeControlSurface:
    def __init__(self, c_instance):
        self.context = c_instance
        self.scheduled = []
    def song(self):
        return self.context.song
    def log_message(self, message):
        pass
    def show_message(self, message):
        pass
    def update_display(self):
        pass
    def disconnect(self):
        pass
    def schedule_message(self, delay, callback, *args):
        self.scheduled.append((delay, callback, args))


def surface_module():
    import remote_script.AbletonArrangementMCP.api  # Keep the exception identity outside patch.dict.
    framework = types.ModuleType("_Framework.ControlSurface")
    framework.ControlSurface = FakeControlSurface
    app = types.SimpleNamespace(get_major_version=lambda: 12, get_minor_version=lambda: 0, get_bugfix_version=lambda: 1)
    live = types.ModuleType("Live")
    live.Application = types.SimpleNamespace(get_application=lambda: app)
    live.Clip = types.SimpleNamespace(MidiNoteSpecification=types.SimpleNamespace)
    with patch.dict(sys.modules, {"Live": live, "_Framework": types.ModuleType("_Framework"), "_Framework.ControlSurface": framework}):
        return importlib.import_module("remote_script.AbletonArrangementMCP.surface")


class SurfaceTests(unittest.TestCase):
    def test_legacy_and_arrangement_dispatch_on_same_main_thread(self):
        module = surface_module()
        self.assertTrue(hasattr(module.ArrangementSurface, "dispatch"), "Combined Live dispatch is missing")
        _, song = make_api()
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "config.json").write_text(json.dumps({"token": "c" * 40, "port": 18765}))
            with patch.object(module, "__file__", str(Path(directory, "surface.py"))):
                surface = module.ArrangementSurface(types.SimpleNamespace(song=song))
            try:
                self.assertIsNotNone(surface._bridge)
                result = surface.dispatch("upstream.set_tempo", {"tempo": 137})
                self.assertEqual(song.tempo, 137)
                self.assertEqual(surface.scheduled, [], "Legacy dispatch must not wait for a queued main-thread task")
                info = surface.dispatch("upstream.get_script_info", {})
                self.assertNotIn("drain_passive_events", info["capabilities"])
                self.assertFalse(info["passive_listeners"])
                self.assertEqual(surface.dispatch("status", {})["tempo"], 137)
                self.assertEqual(surface._bridge.port, 18765)
                with self.assertRaises(module.BridgeError):
                    surface.dispatch("upstream._server_thread", {})
                failures = []
                def off_thread():
                    try:
                        surface.dispatch("upstream.set_tempo", {"tempo": 199})
                    except module.BridgeError as exc:
                        failures.append(exc.code)
                worker = threading.Thread(target=off_thread)
                worker.start()
                worker.join(2)
                self.assertEqual(failures, ["WRONG_THREAD"])
                self.assertEqual(song.tempo, 137)
            finally:
                surface.disconnect()
            self.assertIsNone(surface._bridge)


if __name__ == "__main__":
    unittest.main()
