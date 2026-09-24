import json
import os
import threading
import Live
from _Framework.ControlSurface import ControlSurface
from .api import ArrangementAPI, BridgeError
from .transport import JSONTCPBridge
from .upstream_live import AbletonMCP

UPSTREAM_COMMANDS = frozenset((
    "add_notes_to_clip", "clear_notes_from_clip", "create_audio_clip", "create_audio_track",
    "create_clip", "create_locator", "create_midi_track", "delete_clip", "drain_passive_events",
    "duplicate_session_clip_to_arrangement", "fire_clip", "get_arrangement_clips",
    "get_browser_item", "get_browser_items_at_path", "get_browser_tree", "get_clip_notes",
    "get_device_parameters", "get_script_info", "get_session_info", "get_session_snapshot",
    "get_track_info", "inspect_rack", "load_browser_item", "load_instrument_or_effect",
    "map_rack_magnitude", "set_arrangement_clip_name", "set_clip_name", "set_current_song_time",
    "set_device_parameter", "set_tempo", "set_track_name", "start_playback", "stop_clip",
    "stop_playback", "switch_to_arrangement_view",
))


class ArrangementSurface(AbletonMCP):
    def __init__(self, c_instance):
        # Initialize the framework only; upstream's constructor starts a second TCP server.
        ControlSurface.__init__(self, c_instance)
        self._song = self.song()
        self._owner_thread = threading.get_ident()
        self._dispatching_upstream = False
        self._passive_events = []
        self._passive_lock = threading.Lock()
        self._passive_max = 500
        self._passive_track_count = None
        self._passive_track_bindings = []
        self._song_passive_callbacks = []
        self._capture_passive = False
        self._bridge = None
        try:
            with open(os.path.join(os.path.dirname(__file__), "config.json"), encoding="utf-8") as file:
                config = json.load(file)
            application = Live.Application.get_application()
            version = "%s.%s.%s" % (application.get_major_version(), application.get_minor_version(),
                                    application.get_bugfix_version())
            self._api = ArrangementAPI(self.song(), version, getattr(Live.Clip, "MidiNoteSpecification", None),
                                       os.path.join(os.path.dirname(__file__), "silence.wav"))
            port = config.get("port", 8765)
            if type(port) is not int or not 1024 <= port <= 65535:
                raise ValueError("port must be between 1024 and 65535")
            self._bridge = JSONTCPBridge(self.dispatch, config["token"], port)
            self._capture_passive = bool(config.get("capture_passive_events", False))
            if self._capture_passive:
                self._setup_passive_listeners()
            self.log_message("Arrangement MCP: listening on 127.0.0.1:%s" % port)
            self.show_message("Arrangement MCP ready (Live %s)" % version)
        except Exception as exc:
            if self._bridge is not None:
                self._bridge.close()
                self._bridge = None
            self._teardown_passive_listeners()
            self.log_message("Arrangement MCP startup failed: %s" % exc)
            self.show_message("Arrangement MCP: check config.json and Live Log.txt")

    def update_display(self):
        ControlSurface.update_display(self)
        if self._bridge is not None:
            self._bridge.poll()

    def disconnect(self):
        self._teardown_passive_listeners()
        if self._bridge is not None:
            self._bridge.close()
            self._bridge = None
        ControlSurface.disconnect(self)

    def schedule_message(self, delay, callback, *args):
        if getattr(self, "_dispatching_upstream", False) and delay == 0:
            # Upstream handlers wait on a response queue. Already on the Live thread,
            # execute immediately so they cannot deadlock waiting on themselves.
            callback(*args)
        else:
            return ControlSurface.schedule_message(self, delay, callback, *args)

    def dispatch(self, method, params):
        if threading.get_ident() != self._owner_thread:
            raise BridgeError("WRONG_THREAD", "Live operations must execute on the control-surface thread")
        if method.startswith("upstream."):
            command = method[len("upstream."):]
            if command not in UPSTREAM_COMMANDS or not isinstance(params, dict):
                raise BridgeError("UNKNOWN_METHOD", "Unsupported upstream command")
            self._dispatching_upstream = True
            try:
                response = self._process_command({"type": command, "params": params})
            finally:
                self._dispatching_upstream = False
            if response.get("status") != "success":
                raise BridgeError("LIVE_ERROR", response.get("message", "Upstream operation failed"))
            return response.get("result", {})
        return self._api.call(method, params)

    def _get_script_info(self):
        info = AbletonMCP._get_script_info(self)
        capabilities = set(UPSTREAM_COMMANDS)
        if not self._capture_passive:
            capabilities.discard("drain_passive_events")
        info.update(name="AbletonCtrl", port=self._bridge.port,
                    capabilities=sorted(capabilities), passive_listeners=self._capture_passive,
                    abletonctrl_version="0.3.0", upstream_commit="9dddc7bd5b95412510fdeb745949e3bf23f3fd8a",
                    arrangement_methods=list(self._api.METHODS))
        return info
