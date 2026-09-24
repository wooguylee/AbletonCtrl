"""Native timeline editing with isolated preparation and explicit recovery copies.

No Live start_time/end_time setters, note serialization, or audio re-import of
the source. See doc/timeline-editing-plan.md for assumptions requiring Live tests.
"""
import math
import os
from .api import BridgeError, MAX_BEATS, number, require_method

EPSILON = 0.0001
MAX_SEGMENTS = 64


def near(a, b):
    return math.isclose(a, b, rel_tol=0, abs_tol=EPSILON)


class TimelineEditor:
    def __init__(self, api, track):
        self.api, self.track = api, track
        self.owned = []
        self.committing = False
        self.backup = None
        self.requested_end = 0

    def clips(self):
        return self.api._clips(self.track)

    def bounds(self, clip, start, end):
        if not near(clip.start_time, start) or not near(clip.end_time, end):
            raise BridgeError("RESULT_UNCERTAIN", "Native clip bounds/length differ from requested range; inspect recovery copies")

    def duplicate(self, source, position, length=None, owned=False):
        length = source.end_time - source.start_time if length is None else length
        self.api._space(self.track, position, length)
        before = self.clips()
        require_method(self.track, "duplicate_clip_to_arrangement")(source, float(position))
        created = [c for c in self.clips() if c not in before]
        if len(created) != 1:
            raise BridgeError("RESULT_UNCERTAIN", "Native duplicate did not produce exactly one identifiable clip; list clips")
        clip = created[0]
        if owned:
            self.owned.append(clip)
            clip.muted = True
        self.bounds(clip, position, position + length)
        if clip.is_midi_clip != source.is_midi_clip:
            raise BridgeError("RESULT_UNCERTAIN", "Native duplicate returned a different clip type")
        return clip

    def holding(self, reserve):
        ends = [c.end_time for t in self.api.song.tracks for c in self.api._clips(t)]
        position = max(ends + [self.requested_end, getattr(self.api.song, "current_song_time", 0)]) + 16
        number(position + reserve, "holding area end")
        return position

    def stage(self, source, reserve=None):
        size = source.end_time - source.start_time
        clip = self.duplicate(source, self.holding(max(size, reserve or size)), owned=True)
        return clip

    def remove(self, clip):
        require_method(self.track, "delete_clip")(clip)
        if clip in self.owned:
            self.owned.remove(clip)

    def _audio_cover(self, start, length):
        """Create a silent Session source, then cover an edge (Session source is essential)."""
        path = self.api.silence_path
        if not path or not os.path.isfile(path):
            raise BridgeError("UNSUPPORTED", "Audio timeline editing needs installer-generated silence.wav; reinstall the Remote Script")
        song = self.api.song
        slot = next((s for s in self.track.clip_slots if not s.has_clip), None)
        scene = None
        session_clip = None
        try:
            if slot is None:
                create = require_method(song, "create_scene")
                require_method(song, "delete_scene")
                prior = list(song.scenes)
                create(-1)
                added = [s for s in song.scenes if s not in prior]
                if len(added) != 1:
                    raise BridgeError("RESULT_UNCERTAIN", "Temporary scene was not uniquely identified")
                scene = added[0]
                slot = self.track.clip_slots[list(song.scenes).index(scene)]
            if slot.has_clip:
                raise BridgeError("NOT_EDITABLE", "Temporary Session slot is occupied")
            require_method(slot, "delete_clip")
            require_method(slot, "create_audio_clip")(path)
            session_clip = slot.clip
            session_clip.muted = True
            session_clip.warping = True
            session_clip.looping = True
            session_clip.loop_start = 0.0
            session_clip.loop_end = float(length)
            session_clip.start_marker = 0.0
            if not session_clip.warping or not session_clip.looping or not near(session_clip.length, length):
                raise BridgeError("UNSUPPORTED", "Live did not apply temporary audio warp/loop settings synchronously")
            before = self.clips()
            self.track.duplicate_clip_to_arrangement(session_clip, float(start))
            return self._find_cover(before, start, length)
        finally:
            if session_clip is not None and slot.has_clip and slot.clip == session_clip:
                slot.delete_clip()
            if scene is not None and scene in song.scenes:
                index = list(song.scenes).index(scene)
                if any(t.clip_slots[index].has_clip for t in song.tracks):
                    raise BridgeError("CLEANUP_REQUIRED", "Temporary scene contains unexpected content; retained for inspection")
                song.delete_scene(index)

    def _find_cover(self, before, start, length):
        added = [c for c in self.clips() if c not in before]
        if len(added) != 1:
            raise BridgeError("RESULT_UNCERTAIN", "Temporary edge-cover clip not uniquely identified; inspect holding area")
        cover = added[0]
        self.owned.append(cover)
        cover.muted = True
        self.bounds(cover, start, start + length)
        return cover

    def cover(self, start, end, working):
        # Only the owned working copy may overlap this intentional edge overwrite.
        for clip in self.clips():
            if clip != working and start < clip.end_time and end > clip.start_time:
                raise BridgeError("OVERLAP", "Temporary trim would overlap unrelated content")
        if working.is_midi_clip:
            before = self.clips()
            require_method(self.track, "create_midi_clip")(float(start), float(end - start))
            temporary = self._find_cover(before, start, end - start)
        else:
            temporary = self._audio_cover(start, end - start)
        self.remove(temporary)

    def trim(self, working, start, end):
        original_start, original_end = working.start_time, working.end_time
        if end < original_end - EPSILON:
            self.cover(end, original_end, working)
        if start > original_start + EPSILON:
            self.cover(original_start, start, working)
        self.bounds(working, start, end)
        return working

    def _unlooped(self, source, start, end):
        source_length = source.end_time - source.start_time
        units = 1.0
        if source.is_audio_clip and not source.warping:
            units = (source.loop_end - source.loop_start) / source_length
            number(units, "audio seconds per beat", positive=True)
        content_start = source.loop_start + (start - source.start_time) * units
        content_end = content_start + (end - start) * units
        number(content_start, "content start", low=0 if source.is_audio_clip else -MAX_BEATS)
        number(content_end, "content end", low=-MAX_BEATS)
        if source.is_audio_clip and not source.warping:
            boundary = source.sample_length / float(source.sample_rate)
            if content_end > boundary + EPSILON:
                raise BridgeError("CONTENT_BOUNDARY", "Requested resize exceeds the unwarped audio file boundary")
        working = self.stage(source, end - start)
        # Widen first, so neither intermediate marker order is invalid.
        if not source.is_audio_clip or source.warping:
            working.end_marker = max(working.end_marker, content_end)
        working.loop_end = max(working.loop_end, content_end)
        working.loop_start = float(content_start)
        working.start_marker = float(content_start)
        working.loop_end = float(content_end)
        if not near(working.end_time - working.start_time, end - start):
            raise BridgeError("UNSUPPORTED", "Live did not apply requested unlooped length; original preserved")
        if not near(working.loop_start, content_start) or not near(working.loop_end, content_end):
            raise BridgeError("RESULT_UNCERTAIN", "Native content markers differ from requested resize")
        return [(working, start)]

    def _looped(self, source, start, end):
        period = source.loop_end - source.loop_start
        number(period, "loop length", positive=True)
        if source.is_audio_clip and not source.warping:
            raise BridgeError("UNSUPPORTED", "Unwarped audio cannot use looped resizing")
        duration = source.end_time - source.start_time
        intervals = []
        if start < source.start_time:
            intervals.append((start, min(end, source.start_time), False))
        mid_start, mid_end = max(start, source.start_time), min(end, source.end_time)
        if mid_start < mid_end:
            intervals.append((mid_start, mid_end, True))
        if end > source.end_time:
            intervals.append((max(start, source.end_time), end, False))
        count = sum(1 if middle else int(math.ceil((b-a)/duration)) for a, b, middle in intervals)
        if count > MAX_SEGMENTS:
            raise BridgeError("INVALID_ARGUMENT", "Resize needs more than 64 segments; use smaller ranges")
        prepared = []
        for a, b, middle in intervals:
            while a < b:
                length = b-a if middle else min(duration, b-a)
                working = self.stage(source)
                origin = working.start_time
                if middle:
                    offset = a - source.start_time
                    self.trim(working, origin + offset, origin + offset + length)
                else:
                    content_position = source.start_marker + a - source.start_time
                    has_intro = source.start_marker < source.loop_start
                    phase = (content_position if has_intro and content_position < source.loop_end else
                             source.loop_start + ((content_position - source.loop_start) % period))
                    working.start_marker = float(phase)
                    if not near(working.start_marker, phase) or not working.looping:
                        raise BridgeError("RESULT_UNCERTAIN", "Loop phase update was not applied")
                    self.bounds(working, origin, origin + duration)
                    self.trim(working, origin, origin + length)
                prepared.append((working, a))
                a += length
        return prepared

    def edit(self, clip_id, source, start, end, trim_only=False):
        start = source.start_time if start is None else number(start, "start_beats")
        end = source.end_time if end is None else number(end, "end_beats")
        number(end-start, "length_beats", positive=True)
        self.requested_end = end
        if trim_only and (start < source.start_time or end > source.end_time):
            raise BridgeError("INVALID_ARGUMENT", "Trim bounds must be inside the original clip")
        self.api._editable(self.track, source)
        self.api._space(self.track, start, end-start, exclude=source)
        require_method(self.track, "delete_clip")
        if near(start, source.start_time) and near(end, source.end_time):
            return {"clips": [self.api._snapshot(self.track, source)], "changed": False, "warnings": []}
        original_muted = source.muted
        shrinking = start >= source.start_time and end <= source.end_time

        def apply():
            try:
                if shrinking:
                    working = self.stage(source)
                    offset = working.start_time - source.start_time
                    self.trim(working, start + offset, end + offset)
                    prepared = [(working, start)]
                elif source.looping:
                    prepared = self._looped(source, start, end)
                else:
                    prepared = self._unlooped(source, start, end)
                if not prepared:
                    raise BridgeError("RESULT_UNCERTAIN", "No prepared clips; original preserved")
                self.backup = self.stage(source)
                self.committing = True
                self.track.delete_clip(source)
                self.api.handles.pop(clip_id, None)
                output = []
                for working, destination in prepared:
                    clip = self.duplicate(working, destination)
                    clip.muted = original_muted
                    output.append(self.api._snapshot(self.track, clip))
                for owned in [c for c in reversed(self.owned) if c != self.backup] + [self.backup]:
                    self.remove(owned)
                return {"clips": output, "changed": True,
                        "warnings": ["Looped extension is represented by contiguous native clip segments"] if len(output) > 1 else []}
            except Exception as exc:
                if not self.committing:
                    for owned in list(reversed(self.owned)):
                        try:
                            self.remove(owned)
                        except Exception:
                            pass
                recovery = []
                for clip in self.owned:
                    try:
                        recovery.append(self.api._snapshot(self.track, clip)["clip_id"])
                    except Exception:
                        pass
                code = "PARTIAL_EDIT" if self.committing else getattr(exc, "code", "LIVE_ERROR")
                raise BridgeError(code, "%s; %s. Recovery copies (muted): %s. Inspect the Set before retrying; Live Undo can revert the edit." %
                                  (exc, "original backup retained where available" if self.committing else "original preserved",
                                   ", ".join(recovery) or "none"))
        return self.api._mutate(apply)
