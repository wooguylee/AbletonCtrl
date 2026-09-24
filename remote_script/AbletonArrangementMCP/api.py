"""Live operations. Called only by the Live main thread; no external dependencies."""
import inspect
import math
import os
import uuid
from collections import OrderedDict

MAX_BEATS = 1576800.0


class BridgeError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def number(value, name, low=0, high=MAX_BEATS, positive=False, integer=False):
    valid = type(value) in (int, float) and math.isfinite(value)
    if not valid or not low <= value <= high or (positive and value <= 0):
        raise BridgeError("INVALID_ARGUMENT", "Invalid %s" % name)
    if integer and type(value) is not int:
        raise BridgeError("INVALID_ARGUMENT", "%s must be an integer" % name)
    return value


def require_method(obj, name):
    method = getattr(obj, name, None)
    if not callable(method):
        raise BridgeError("UNSUPPORTED", "This Live build does not expose %s" % name)
    return method


class ArrangementAPI:
    METHODS = ("status", "list_tracks", "list_clips", "get_clip", "update_clip",
               "create_midi_clip", "create_audio_clip", "duplicate_clip", "move_clip",
               "delete_clip", "get_notes", "add_notes", "update_notes", "delete_notes",
               "copy_clip", "trim_clip", "resize_clip")

    def __init__(self, song, version, note_factory, silence_path=None):
        self.song = song
        self.version = version
        self.note_factory = note_factory
        self.handles = OrderedDict()
        self.silence_path = silence_path

    def call(self, method, params):
        if method not in self.METHODS:
            raise BridgeError("UNKNOWN_METHOD", "Unknown method")
        if not isinstance(params, dict):
            raise BridgeError("INVALID_ARGUMENT", "params must be an object")
        function = getattr(self, method)
        try:
            inspect.signature(function).bind(**params)
        except TypeError as exc:
            raise BridgeError("INVALID_ARGUMENT", str(exc))
        try:
            return function(**params)
        except BridgeError:
            raise
        except Exception as exc:
            raise BridgeError("LIVE_ERROR", "%s. A write may be partial; inspect the Set and use Live Undo if needed." % exc)

    def _handle(self, kind, obj, owner=None):
        for key, item in list(self.handles.items()):
            try:
                if item[0] == kind and item[1] == obj and item[2] == owner:
                    self.handles.move_to_end(key)
                    return key
            except RuntimeError:
                self.handles.pop(key, None)
        key = kind + "-" + uuid.uuid4().hex
        self.handles[key] = (kind, obj, owner)
        while len(self.handles) > 4096:
            self.handles.popitem(last=False)
        return key

    def _resolve(self, key, kind):
        if not isinstance(key, str):
            raise BridgeError("INVALID_ARGUMENT", "Handle must be a string")
        item = self.handles.get(key)
        try:
            if item and item[0] == kind:
                obj, owner = item[1:]
                if kind == "track" and obj in self.song.tracks:
                    return obj
                if kind == "clip" and owner in self.song.tracks and obj in owner.arrangement_clips:
                    return owner, obj
        except (RuntimeError, AttributeError):
            pass
        self.handles.pop(key, None)
        raise BridgeError("STALE_HANDLE", "Target no longer exists or handle expired; list again")

    @staticmethod
    def _clips(track):
        if not hasattr(track, "arrangement_clips"):
            raise BridgeError("UNSUPPORTED", "arrangement_clips is unavailable")
        return list(track.arrangement_clips)

    def _editable(self, track, clip=None):
        if (track.is_frozen or getattr(self.song, "record_mode", False)
                or getattr(self.song, "session_record", False)
                or any(getattr(c, "is_recording", False) for c in self._clips(track))
                or (clip is not None and getattr(clip, "is_recording", False))):
            raise BridgeError("NOT_EDITABLE", "Stop recording and unfreeze the target track before editing")

    def _mutate(self, action):
        begin = require_method(self.song, "begin_undo_step")
        end = require_method(self.song, "end_undo_step")
        begin()
        try:
            return action()
        finally:
            end()

    def _snapshot(self, track, clip):
        return {"clip_id": self._handle("clip", clip, track),
                "track_id": self._handle("track", track), "name": clip.name,
                "type": "midi" if clip.is_midi_clip else "audio",
                "start_beats": clip.start_time, "end_beats": clip.end_time,
                "duration_beats": clip.end_time - clip.start_time,
                "color": clip.color, "muted": bool(clip.muted),
                "looping": bool(clip.looping), "loop_start": clip.loop_start,
                "loop_end": clip.loop_end,
                "clip_time_unit": "seconds" if clip.is_audio_clip and not getattr(clip, "warping", False) else "beats"}

    @staticmethod
    def _page(items, offset, limit):
        number(offset, "offset", integer=True)
        number(limit, "limit", low=1, high=100, integer=True)
        return items[offset:offset + limit]

    def status(self):
        return {"bridge_version": "0.3.0", "live_version": self.version,
                "time_unit": "beats", "tempo": self.song.tempo,
                "time_signature": [self.song.signature_numerator, self.song.signature_denominator],
                "is_playing": bool(self.song.is_playing), "track_count": len(self.song.tracks),
                "methods": list(self.METHODS), "note_factory_available": callable(self.note_factory)}

    def list_tracks(self, offset=0, limit=100):
        tracks = list(enumerate(self.song.tracks))
        result = []
        for index, track in self._page(tracks, offset, limit):
            result.append({"track_id": self._handle("track", track), "index": index,
                           "name": track.name, "is_midi": bool(track.has_midi_input),
                           "is_audio": bool(track.has_audio_input), "is_group": bool(track.is_foldable),
                           "is_frozen": bool(track.is_frozen),
                           "capabilities": {name: callable(getattr(track, name, None)) for name in
                                            ("create_midi_clip", "create_audio_clip", "duplicate_clip_to_arrangement", "delete_clip")},
                           "arrangement_available": hasattr(track, "arrangement_clips")})
        return {"tracks": result, "total": len(tracks), "offset": offset}

    def list_clips(self, track_id, offset=0, limit=100):
        track = self._resolve(track_id, "track")
        clips = self._clips(track)
        return {"clips": [self._snapshot(track, c) for c in self._page(clips, offset, limit)],
                "total": len(clips), "offset": offset}

    def get_clip(self, clip_id):
        return self._snapshot(*self._resolve(clip_id, "clip"))

    def update_clip(self, clip_id, name=None, color=None, muted=None):
        track, clip = self._resolve(clip_id, "clip")
        self._editable(track, clip)
        changes = {}
        if name is not None:
            if not isinstance(name, str) or len(name) > 256:
                raise BridgeError("INVALID_ARGUMENT", "name must be a string up to 256 characters")
            changes["name"] = name
        if color is not None:
            changes["color"] = number(color, "color", high=0xFFFFFF, integer=True)
        if muted is not None:
            if type(muted) is not bool:
                raise BridgeError("INVALID_ARGUMENT", "muted must be a boolean")
            changes["muted"] = muted
        if not changes:
            raise BridgeError("INVALID_ARGUMENT", "Supply name, color, or muted")
        def apply():
            for key, value in changes.items():
                setattr(clip, key, value)
            return self._snapshot(track, clip)
        return self._mutate(apply)

    def _space(self, track, start, length, exclude=None):
        number(start, "start_beats")
        number(length, "length_beats", positive=True)
        number(start + length, "end_beats")
        for clip in self._clips(track):
            if clip == exclude:
                continue
            if start < clip.end_time and start + length > clip.start_time:
                raise BridgeError("OVERLAP", "Destination overlaps an existing Arrangement clip")

    def _insert(self, track, action):
        before = self._clips(track)
        def apply():
            action()
            added = [c for c in self._clips(track) if c not in before]
            if len(added) != 1:
                raise BridgeError("RESULT_UNCERTAIN", "Native call completed but new clip was not uniquely found; list clips before any retry")
            return self._snapshot(track, added[0])
        return self._mutate(apply)

    def create_midi_clip(self, track_id, start_beats, length_beats):
        track = self._resolve(track_id, "track")
        if not track.has_midi_input:
            raise BridgeError("WRONG_TRACK_TYPE", "MIDI clips require a MIDI track")
        self._editable(track)
        create = require_method(track, "create_midi_clip")
        self._space(track, start_beats, length_beats)
        return self._insert(track, lambda: create(float(start_beats), float(length_beats)))

    def duplicate_clip(self, clip_id, destination_beats):
        track, clip = self._resolve(clip_id, "clip")
        return self.copy_clip(clip_id, self._handle("track", track), destination_beats)

    def _copy_target(self, source_track, clip, target_track_id):
        target = self._resolve(target_track_id, "track")
        if target.is_foldable or not (target.has_midi_input if clip.is_midi_clip else target.has_audio_input):
            raise BridgeError("WRONG_TRACK_TYPE", "Source clip and destination track type must match")
        self._editable(source_track, clip)
        self._editable(target)
        require_method(target, "duplicate_clip_to_arrangement")
        return target

    def copy_clip(self, clip_id, target_track_id, destination_beats):
        from .timeline import TimelineEditor
        source_track, clip = self._resolve(clip_id, "clip")
        target = self._copy_target(source_track, clip, target_track_id)
        self._space(target, destination_beats, clip.end_time - clip.start_time)
        def apply():
            copied = TimelineEditor(self, target).duplicate(clip, destination_beats)
            return self._snapshot(target, copied)
        return self._mutate(apply)

    def trim_clip(self, clip_id, start_beats, end_beats):
        from .timeline import TimelineEditor
        track, clip = self._resolve(clip_id, "clip")
        return TimelineEditor(self, track).edit(clip_id, clip, start_beats, end_beats, trim_only=True)

    def resize_clip(self, clip_id, start_beats=None, end_beats=None):
        from .timeline import TimelineEditor
        track, clip = self._resolve(clip_id, "clip")
        return TimelineEditor(self, track).edit(clip_id, clip, start_beats, end_beats)

    def create_audio_clip(self, track_id, file_path, start_beats):
        track = self._resolve(track_id, "track")
        if not track.has_audio_input:
            raise BridgeError("WRONG_TRACK_TYPE", "Audio clips require an audio track")
        self._editable(track)
        create = require_method(track, "create_audio_clip")
        number(start_beats, "start_beats")
        if not isinstance(file_path, str) or not os.path.isabs(file_path) or not os.path.isfile(file_path):
            raise BridgeError("INVALID_ARGUMENT", "file_path must be an existing absolute file on the Live computer")
        # Imported length depends on Live's warp settings and is unknown before insertion.
        if any(start_beats < c.end_time for c in self._clips(track)):
            raise BridgeError("OVERLAP", "Import audio at or after the last clip on this track")
        return self._insert(track, lambda: create(file_path, float(start_beats)))

    def move_clip(self, clip_id, destination_beats, target_track_id=None):
        track, clip = self._resolve(clip_id, "clip")
        target = self._copy_target(track, clip, target_track_id or self._handle("track", track))
        number(destination_beats, "destination_beats")
        if target == track and destination_beats == clip.start_time:
            return self._snapshot(track, clip)
        duplicate = require_method(target, "duplicate_clip_to_arrangement")
        delete = require_method(track, "delete_clip")
        length = clip.end_time - clip.start_time
        self._space(target, destination_beats, length)
        before = self._clips(target)
        def apply():
            duplicate(clip, float(destination_beats))
            added = [c for c in self._clips(target) if c not in before]
            if (len(added) != 1 or not math.isclose(added[0].start_time, destination_beats, abs_tol=1e-6)
                    or not math.isclose(added[0].end_time - added[0].start_time, length, abs_tol=1e-6)
                    or added[0].is_midi_clip != clip.is_midi_clip):
                raise BridgeError("RESULT_UNCERTAIN", "Could not verify the copy; original preserved. List clips before retrying")
            copied = self._snapshot(target, added[0])
            try:
                delete(clip)
            except Exception as exc:
                raise BridgeError("PARTIAL_MOVE", "Could not delete original; inspect original %s and copy %s before retrying: %s" %
                                  (clip_id, copied["clip_id"], exc))
            self.handles.pop(clip_id, None)
            return copied
        return self._mutate(apply)

    def delete_clip(self, clip_id):
        track, clip = self._resolve(clip_id, "clip")
        self._editable(track, clip)
        delete = require_method(track, "delete_clip")
        snapshot = self._snapshot(track, clip)
        self._mutate(lambda: delete(clip))
        self.handles.pop(clip_id, None)
        return {"deleted": snapshot}

    def _midi(self, clip_id):
        track, clip = self._resolve(clip_id, "clip")
        if not clip.is_midi_clip:
            raise BridgeError("WRONG_CLIP_TYPE", "MIDI notes require a MIDI clip")
        return track, clip

    def get_notes(self, clip_id, start_beats=0.0, length_beats=16.0, limit=1000):
        _, clip = self._midi(clip_id)
        number(start_beats, "start_beats", low=-MAX_BEATS)
        number(length_beats, "length_beats", positive=True)
        number(limit, "limit", low=1, high=1000, integer=True)
        notes = require_method(clip, "get_notes_extended")(0, 128, float(start_beats), float(length_beats))
        keys = ("note_id", "pitch", "start_time", "duration", "velocity", "mute", "probability",
                "velocity_deviation", "release_velocity")
        return {"notes": [{key: getattr(n, key) for key in keys if hasattr(n, key)} for n in notes[:limit]],
                "total_in_range": len(notes), "truncated": len(notes) > limit, "time_unit": "clip_beats"}

    def add_notes(self, clip_id, notes):
        track, clip = self._midi(clip_id)
        self._editable(track, clip)
        add = require_method(clip, "add_new_notes")
        if not callable(self.note_factory):
            raise BridgeError("UNSUPPORTED", "Live.Clip.MidiNoteSpecification is unavailable")
        if not isinstance(notes, list) or not 1 <= len(notes) <= 256:
            raise BridgeError("INVALID_ARGUMENT", "Supply 1 to 256 MIDI notes")
        specs = []
        for note in notes:
            if not isinstance(note, dict) or set(note) - {"pitch", "start_time", "duration", "velocity", "mute"}:
                raise BridgeError("INVALID_ARGUMENT", "Unknown MIDI note fields")
            if not {"pitch", "start_time", "duration"}.issubset(note):
                raise BridgeError("INVALID_ARGUMENT", "pitch, start_time and duration are required")
            fields = dict(note)
            fields["pitch"] = number(note["pitch"], "pitch", high=127, integer=True)
            fields["start_time"] = float(number(note["start_time"], "start_time", low=-MAX_BEATS))
            fields["duration"] = float(number(note["duration"], "duration", positive=True))
            number(fields["start_time"] + fields["duration"], "note_end", low=-MAX_BEATS)
            fields["velocity"] = float(number(note.get("velocity", 100), "velocity", high=127))
            fields["mute"] = note.get("mute", False)
            if type(fields["mute"]) is not bool:
                raise BridgeError("INVALID_ARGUMENT", "mute must be boolean")
            specs.append(self.note_factory(**fields))
        self._mutate(lambda: add(tuple(specs)))
        return {"clip_id": clip_id, "added_count": len(specs)}

    @staticmethod
    def _notes_by_id(clip, note_ids):
        if not isinstance(note_ids, list) or not 1 <= len(note_ids) <= 256:
            raise BridgeError("INVALID_ARGUMENT", "Supply 1 to 256 note IDs")
        for note_id in note_ids:
            number(note_id, "note_id", high=2**53 - 1, integer=True)
        if len(set(note_ids)) != len(note_ids):
            raise BridgeError("INVALID_ARGUMENT", "Duplicate note IDs")
        notes = require_method(clip, "get_notes_by_id")(tuple(note_ids))
        if set(n.note_id for n in notes) != set(note_ids):
            raise BridgeError("STALE_NOTE_IDS", "Some note IDs no longer exist; read notes again")
        return notes

    def update_notes(self, clip_id, notes):
        track, clip = self._midi(clip_id)
        self._editable(track, clip)
        apply = require_method(clip, "apply_note_modifications")
        if not isinstance(notes, list) or not 1 <= len(notes) <= 256:
            raise BridgeError("INVALID_ARGUMENT", "Supply 1 to 256 note updates")
        updates = {}
        for note in notes:
            if (not isinstance(note, dict) or "note_id" not in note or len(note) < 2
                    or set(note) - {"note_id", "pitch", "start_time", "duration", "velocity", "mute"}):
                raise BridgeError("INVALID_ARGUMENT", "Each update needs note_id and supported note fields")
            note_id = number(note["note_id"], "note_id", high=2**53 - 1, integer=True)
            if note_id in updates:
                raise BridgeError("INVALID_ARGUMENT", "Duplicate note IDs")
            fields = dict(note)
            del fields["note_id"]
            for key, value in fields.items():
                if key == "mute":
                    if type(value) is not bool:
                        raise BridgeError("INVALID_ARGUMENT", "mute must be boolean")
                else:
                    number(value, key, low=-MAX_BEATS if key == "start_time" else 0,
                           high=127 if key in ("pitch", "velocity") else MAX_BEATS,
                           positive=key == "duration", integer=key == "pitch")
            updates[note_id] = fields
        native_notes = self._notes_by_id(clip, list(updates))
        for note in native_notes:
            fields = updates[note.note_id]
            number(fields.get("start_time", note.start_time) + fields.get("duration", note.duration),
                   "note_end", low=-MAX_BEATS)
        def write():
            for note in native_notes:
                for key, value in updates[note.note_id].items():
                    setattr(note, key, value)
            apply(native_notes)
        self._mutate(write)
        return {"clip_id": clip_id, "updated_count": len(updates)}

    def delete_notes(self, clip_id, note_ids):
        track, clip = self._midi(clip_id)
        self._editable(track, clip)
        remove = require_method(clip, "remove_notes_by_id")
        self._notes_by_id(clip, note_ids)
        self._mutate(lambda: remove(tuple(note_ids)))
        return {"clip_id": clip_id, "deleted_count": len(note_ids)}
