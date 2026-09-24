from copy import deepcopy
from types import SimpleNamespace


class Clip:
    def __init__(self, start=0.0, length=4.0, midi=True):
        self.start_time = start
        self.end_time = start + length
        self.length = length
        self.name = "Test clip"
        self.color = 0xFF0000
        self.muted = False
        self.is_midi_clip = midi
        self.is_audio_clip = not midi
        self.is_arrangement_clip = True
        self.is_recording = False
        self.is_playing = False
        self.loop_start = 0.0
        self.loop_end = length
        self.start_marker = 0.0
        self.end_marker = length
        self.looping = False
        self.notes = []

    def set_notes(self, notes):
        self.add_new_notes([SimpleNamespace(pitch=n[0], start_time=n[1], duration=n[2], velocity=n[3], mute=n[4]) for n in notes])

    def fire(self):
        self.is_playing = True

    def stop(self):
        self.is_playing = False

    def get_notes_extended(self, pitch, span, start, length):
        return [n for n in self.notes if pitch <= n.pitch < pitch + span
                and start <= n.start_time < start + length]

    def add_new_notes(self, notes):
        for note in notes:
            note.note_id = len(self.notes) + 1
            self.notes.append(note)

    def get_notes_by_id(self, ids):
        return [deepcopy(n) for n in self.notes if n.note_id in ids]

    def apply_note_modifications(self, notes):
        replacements = {n.note_id: n for n in notes}
        self.notes = [replacements.get(n.note_id, n) for n in self.notes]

    def remove_notes_by_id(self, ids):
        self.notes = [n for n in self.notes if n.note_id not in ids]


class ClipSlot:
    def __init__(self):
        self.clip = None

    @property
    def has_clip(self):
        return self.clip is not None

    def create_clip(self, length):
        self.clip = Clip(length=length)
        self.clip.is_arrangement_clip = False

    def create_audio_clip(self, path):
        self.clip = Clip(length=8, midi=False)
        self.clip.is_arrangement_clip = False

    def delete_clip(self):
        self.clip = None

    def fire(self):
        self.clip.fire()

    def stop(self):
        self.clip.stop()


class Track:
    def __init__(self, midi=True):
        self.name = "MIDI" if midi else "Audio"
        self.has_midi_input = midi
        self.has_audio_input = not midi
        self.is_foldable = False
        self.is_frozen = False
        self.mute = self.solo = self.arm = False
        self.can_be_armed = True
        self.clip_slots = [ClipSlot(), ClipSlot()]
        self.mixer_device = SimpleNamespace(volume=SimpleNamespace(value=0.8), panning=SimpleNamespace(value=0.0), sends=[])
        parameter = SimpleNamespace(name="Gain", value=0.5, min=0.0, max=1.0, is_enabled=True, is_quantized=False)
        self.devices = [SimpleNamespace(name="Test effect", class_name="AudioEffect", type=1, can_have_chains=False, parameters=[parameter])]
        self.arrangement_clips = [Clip(midi=midi)]

    def create_midi_clip(self, start, length):
        self.arrangement_clips.append(Clip(start, length))
        # Native mutators may return None: callers must inspect actual state.

    def duplicate_clip_to_arrangement(self, clip, position):
        copied = deepcopy(clip)
        copied.start_time = position
        copied.end_time = position + clip.end_time - clip.start_time
        self.arrangement_clips.append(copied)

    def delete_clip(self, clip):
        self.arrangement_clips.remove(clip)

    def create_audio_clip(self, path, start):
        self.arrangement_clips.append(Clip(start, 8, midi=False))


class Song:
    def __init__(self):
        self.tracks = [Track(), Track(False)]
        self.return_tracks = []
        self.master_track = Track(False)
        self.scenes = []
        self.cue_points = []
        self.current_song_time = 0.0
        self.tempo = 120.0
        self.signature_numerator = 4
        self.signature_denominator = 4
        self.is_playing = False
        self.record_mode = False
        self.session_record = False
        self.undo_depth = 0
        self.undo_count = 0

    def create_midi_track(self, index):
        self.tracks.insert(len(self.tracks) if index == -1 else index, Track())

    def create_audio_track(self, index):
        self.tracks.insert(len(self.tracks) if index == -1 else index, Track(False))

    def start_playing(self):
        self.is_playing = True

    def stop_playing(self):
        self.is_playing = False

    def begin_undo_step(self):
        self.undo_depth += 1
        self.undo_count += 1

    def end_undo_step(self):
        self.undo_depth -= 1


def make_api():
    from remote_script.AbletonArrangementMCP.api import ArrangementAPI
    song = Song()
    return ArrangementAPI(song, "12.fake", SimpleNamespace), song
