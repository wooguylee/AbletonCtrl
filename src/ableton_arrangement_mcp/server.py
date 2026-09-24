import argparse
import asyncio
import json
import os
import sys
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field
from .client import BridgeClient, BridgeClientError
from .compatibility import register_upstream_tools, compatibility_lifespan

Beat = Annotated[float, Field(ge=0, le=1576800, strict=True, allow_inf_nan=False)]
Duration = Annotated[float, Field(gt=0, le=1576800, strict=True, allow_inf_nan=False)]
ClipBeat = Annotated[float, Field(ge=-1576800, le=1576800, strict=True, allow_inf_nan=False)]
Offset = Annotated[int, Field(ge=0, le=1576800, strict=True)]
PageSize = Annotated[int, Field(ge=1, le=100, strict=True)]
Color = Annotated[int, Field(ge=0, le=0xFFFFFF, strict=True)]
Name = Annotated[str, Field(max_length=256, strict=True)]
NoteId = Annotated[int, Field(ge=0, le=2**53 - 1, strict=True)]


class MidiNote(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    pitch: Annotated[int, Field(ge=0, le=127)]
    start_time: ClipBeat
    duration: Duration
    velocity: Annotated[float, Field(ge=0, le=127, allow_inf_nan=False)] = 100.0
    mute: bool = False


class MidiNoteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    note_id: NoteId
    pitch: Annotated[int, Field(ge=0, le=127)] | None = None
    start_time: ClipBeat | None = None
    duration: Duration | None = None
    velocity: Annotated[float, Field(ge=0, le=127, allow_inf_nan=False)] | None = None
    mute: bool | None = None


READ = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
ADD = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False)
EDIT = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=True, openWorldHint=False)
DELETE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=False)


def create_server(client: BridgeClient) -> FastMCP:
    mcp = FastMCP("AbletonCtrl", log_level="WARNING", lifespan=compatibility_lifespan, instructions=(
        "Control Ableton Live 12 using the original ableton-mcp tools plus extended Arrangement tools. "
        "Original tools retain zero-based track/clip indices; re-list after structural changes. "
        "For ableton_ prefixed tools, first list tracks and clips; "
        "use returned opaque handles, never guessed indices. Song positions are zero-based quarter-note beats. "
        "MIDI note positions are clip-local beats. No automatic retries after timeout: inspect state. "
        "Creation/duplication rejects overlaps. Do not describe writes as saved to disk. "
        "Changing metadata is not moving or trimming clips. Live Undo is available but edits are not transactions."))

    async def call(method, **params):
        return await asyncio.to_thread(client.call, method, params)

    @mcp.tool(annotations=READ)
    async def ableton_status() -> dict[str, Any]:
        """Read bridge connectivity, native Live version, tempo, meter and available bridge methods."""
        return await call("status")

    @mcp.tool(annotations=READ)
    async def ableton_list_tracks(offset: Offset = 0, limit: PageSize = 100) -> dict[str, Any]:
        """List normal tracks and their opaque track_id handles, types and native API capabilities."""
        return await call("list_tracks", offset=offset, limit=limit)

    @mcp.tool(annotations=READ)
    async def ableton_list_arrangement_clips(track_id: str, offset: Offset = 0, limit: PageSize = 100) -> dict[str, Any]:
        """List a track's Arrangement clips. Return stable clip_id handles and song start/end in beats."""
        return await call("list_clips", track_id=track_id, offset=offset, limit=limit)

    @mcp.tool(annotations=READ)
    async def ableton_get_arrangement_clip(clip_id: str) -> dict[str, Any]:
        """Inspect the current state of an Arrangement clip using a previously listed clip_id."""
        return await call("get_clip", clip_id=clip_id)

    @mcp.tool(annotations=EDIT)
    async def ableton_update_arrangement_clip(clip_id: str, name: Name | None = None,
                                              color: Color | None = None,
                                              muted: Annotated[bool, Field(strict=True)] | None = None) -> dict[str, Any]:
        """Set name, RGB color (nearest Live palette color), or muted. Does not move/resize the clip."""
        return await call("update_clip", clip_id=clip_id, name=name, color=color, muted=muted)

    @mcp.tool(annotations=ADD)
    async def ableton_create_arrangement_midi_clip(track_id: str, start_beats: Beat, length_beats: Duration) -> dict[str, Any]:
        """Create an empty MIDI Arrangement clip on an existing MIDI track. Refuse overlapping clips."""
        return await call("create_midi_clip", track_id=track_id, start_beats=start_beats, length_beats=length_beats)

    @mcp.tool(annotations=ADD)
    async def ableton_create_arrangement_audio_clip(track_id: str, file_path: str, start_beats: Beat) -> dict[str, Any]:
        """Import an existing absolute audio file on the Live PC at/after the track's LAST clip. Length depends on Live warp settings."""
        return await asyncio.to_thread(client.call, "create_audio_clip",
                                       {"track_id": track_id, "file_path": file_path, "start_beats": start_beats}, timeout=70)

    @mcp.tool(annotations=ADD)
    async def ableton_duplicate_arrangement_clip(clip_id: str, destination_beats: Beat) -> dict[str, Any]:
        """Duplicate a MIDI/audio Arrangement clip on the SAME track at a free song position in beats."""
        return await call("duplicate_clip", clip_id=clip_id, destination_beats=destination_beats)

    @mcp.tool(annotations=DELETE)
    async def ableton_move_arrangement_clip(clip_id: str, destination_beats: Beat) -> dict[str, Any]:
        """Move on the SAME track by verified copy then delete in one Undo step. Return a NEW clip_id. Destination must not overlap any clip, including source; partial failures require inspection."""
        return await call("move_clip", clip_id=clip_id, destination_beats=destination_beats)

    @mcp.tool(annotations=DELETE)
    async def ableton_delete_arrangement_clip(clip_id: str) -> dict[str, Any]:
        """Delete the identified Arrangement clip from the current Set. Destructive; grouped for Live Undo."""
        return await call("delete_clip", clip_id=clip_id)

    @mcp.tool(annotations=READ)
    async def ableton_get_midi_notes(clip_id: str, start_beats: ClipBeat = 0.0,
                                    length_beats: Duration = 16.0,
                                    limit: Annotated[int, Field(ge=1, le=1000, strict=True)] = 1000) -> dict[str, Any]:
        """Read MIDI notes whose onset is in a clip-local beat range; narrow the range if truncated."""
        return await call("get_notes", clip_id=clip_id, start_beats=start_beats, length_beats=length_beats, limit=limit)

    @mcp.tool(annotations=ADD)
    async def ableton_add_midi_notes(clip_id: str,
                                    notes: Annotated[list[MidiNote], Field(min_length=1, max_length=256)]) -> dict[str, Any]:
        """Add 1-256 notes without replacing existing notes. start_time is clip-local beats; pitch is MIDI 0-127."""
        return await call("add_notes", clip_id=clip_id, notes=[n.model_dump() for n in notes])

    @mcp.tool(annotations=EDIT)
    async def ableton_update_midi_notes(clip_id: str,
                                      notes: Annotated[list[MidiNoteUpdate], Field(min_length=1, max_length=256)]) -> dict[str, Any]:
        """Update notes by note_id from ableton_get_midi_notes; omit unchanged fields. Fails if any ID is stale."""
        return await call("update_notes", clip_id=clip_id, notes=[n.model_dump(exclude_none=True) for n in notes])

    @mcp.tool(annotations=DELETE)
    async def ableton_delete_midi_notes(clip_id: str,
                                      note_ids: Annotated[list[NoteId], Field(min_length=1, max_length=256)]) -> dict[str, Any]:
        """Delete specific MIDI notes by current note_id, preserving all other notes. Fails if any ID is stale."""
        return await call("delete_notes", clip_id=clip_id, note_ids=note_ids)

    register_upstream_tools(mcp, client)
    return mcp


def main():
    parser = argparse.ArgumentParser(description="Ableton Arrangement MCP (stdio)")
    parser.add_argument("--config", default=os.environ.get("ABLETON_MCP_CONFIG"), help="Absolute path to bridge JSON config")
    parser.add_argument("--check", action="store_true", help="Read Live status once and exit; no Set edits")
    args = parser.parse_args()
    if not args.config:
        parser.error("Use --config or set ABLETON_MCP_CONFIG; run scripts/configure.py first")
    try:
        client = BridgeClient.from_file(args.config)
        if args.check:
            print(json.dumps(client.call("status"), ensure_ascii=True, indent=2))
        else:
            create_server(client).run(transport="stdio")
    except (OSError, ValueError, KeyError, BridgeClientError) as exc:
        print("Ableton Arrangement MCP: %s" % exc, file=sys.stderr)
        raise SystemExit(1)
