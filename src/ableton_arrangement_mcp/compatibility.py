"""Adapt pinned ahujasid tools to the authenticated bridge. Collection is default-off."""
import asyncio
import contextvars
import functools
import inspect
import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from mcp.types import ToolAnnotations

UPSTREAM_COMMIT = "9dddc7bd5b95412510fdeb745949e3bf23f3fd8a"
UPSTREAM_TOOLS = (
    "set_dataset_consent", "get_session_info", "get_remote_script_info", "get_track_info",
    "get_clip_notes", "get_device_parameters", "set_device_parameter", "get_session_snapshot",
    "create_midi_track", "create_audio_track", "set_track_name", "create_clip", "create_audio_clip",
    "add_notes_to_clip", "clear_notes_from_clip", "set_clip_name", "set_arrangement_clip_name",
    "set_tempo", "load_instrument_or_effect", "fire_clip", "stop_clip", "delete_clip",
    "start_playback", "stop_playback", "get_browser_tree", "get_browser_items_at_path",
    "load_drum_kit", "switch_to_arrangement_view", "set_arrangement_time", "get_arrangement_clips",
    "duplicate_to_arrangement", "create_locator", "submit_intent", "rate_last_action",
    "prefer_candidate", "reject_last_action", "record_audition",
)
DATASET_TOOLS = frozenset(("set_dataset_consent", "submit_intent", "rate_last_action",
                           "prefer_candidate", "reject_last_action", "record_audition"))
_connection = contextvars.ContextVar("abletonctrl_upstream_connection")
_lock = threading.RLock()  # Upstream handshake state is global; guard each complete legacy call.


class _ClientContext:
    """Keep consent elicitation on the MCP session's event loop."""
    def __init__(self, context, loop):
        self._context, self._loop = context, loop

    def __getattr__(self, name):
        return getattr(self._context, name)

    async def elicit(self, *args, **kwargs):
        future = asyncio.run_coroutine_threadsafe(self._context.elicit(*args, **kwargs), self._loop)
        return await asyncio.wrap_future(future)


class UpstreamConnection:
    def __init__(self, client):
        self.client = client

    def send_command(self, command_type, params=None):
        options = {}
        if command_type in {"create_audio_clip", "get_session_snapshot", "get_browser_tree", "get_browser_items_at_path", "load_browser_item"}:
            options["timeout"] = 70
        return self.client.call("upstream." + command_type, params or {}, **options)


@asynccontextmanager
async def compatibility_lifespan(mcp):
    from .upstream.dataset import dataset_enabled, get_recorder
    from .upstream.dataset.passive_poller import start_passive_poller, stop_passive_poller
    try:
        if dataset_enabled():
            start_passive_poller()
        yield {}
    finally:
        await asyncio.to_thread(stop_passive_poller)
        recorder = get_recorder() if dataset_enabled() else None
        if recorder is not None:
            await asyncio.to_thread(recorder.end, timeout=5)


def register_upstream_tools(mcp, client):
    # Import after setting local state/collection policy. No app-global memory or upload by default.
    state_dir = getattr(client, "state_dir", Path.cwd() / "doc" / "local" / "upstream")
    os.environ["ABLETON_MCP_STATE_DIR"] = str(state_dir)
    os.environ.setdefault("ABLETON_MCP_DISABLE_TELEMETRY", "true")
    os.environ.setdefault("ABLETON_MCP_DISABLE_DATASET", "true")
    from .upstream import server as upstream
    from .upstream import script_handshake
    from .upstream.telemetry import TelemetryCollector
    from .upstream.dataset import consent
    # Also handle modules imported before server construction (e.g. test discovery).
    if consent._STATE_DIR != Path(state_dir):
        consent._STATE_DIR = Path(state_dir)
        consent._STATE_FILE = Path(state_dir) / "consent.json"
        consent._cache = None
    # Preserve the collector implementation, redirect only its local storage location.
    def data_directory(self):
        path = Path(os.environ["ABLETON_MCP_STATE_DIR"])
        path.mkdir(parents=True, exist_ok=True)
        return path
    TelemetryCollector._get_data_directory = data_directory
    adapter = UpstreamConnection(client)
    # One server per process; background passive poller threads have no ContextVar.
    upstream.get_ableton_connection = lambda: _connection.get(adapter)

    def wrap(function, name):
        @functools.wraps(function)
        async def invoke(*args, **kwargs):
            if kwargs.get("ctx") is not None:
                kwargs["ctx"] = _ClientContext(kwargs["ctx"], asyncio.get_running_loop())
            def run():
                with _lock:
                    context_token = _connection.set(adapter)
                    try:
                        if name not in DATASET_TOOLS:
                            # Do not use a capability cache from a previous Set or server instance.
                            script_handshake.handshake(adapter.send_command)
                        result = function(*args, **kwargs)
                        # Upstream trajectory decorators expose async wrappers even
                        # around synchronous tool bodies. Run them off the MCP loop.
                        return asyncio.run(result) if inspect.isawaitable(result) else result
                    finally:
                        _connection.reset(context_token)
            return await asyncio.to_thread(run)
        return invoke

    for name in UPSTREAM_TOOLS:
        # Preserve original decorators, including optional dataset workflows.
        # Their existing consent gates and default kill switches prevent collection.
        function = getattr(upstream, name)
        read = name.startswith("get_")
        mcp.add_tool(wrap(function, name), name=name,
                     annotations=ToolAnnotations(readOnlyHint=read, destructiveHint=not read,
                                                 idempotentHint=read, openWorldHint=name in DATASET_TOOLS))
