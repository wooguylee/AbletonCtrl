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
        self.loop_start = 0.0
        self.loop_end = length
        self.start_marker = 0.0
        self.end_marker = length
        self.looping = False
        self.notes = []

    def get_notes_extended(self, pitch, span, start, length):
        return [n for n in self.notes if pitch <= n.pitch < pitch + span
                and start <= n.start_time < start + length]

    def add_new_notes(self, notes):
        for note in notes:
            note.note_id = len(self.notes) + 1
            self.notes.append(note)


class Track:
    def __init__(self, midi=True):
        self.name = "MIDI" if midi else "Audio"
        self.has_midi_input = midi
        self.has_audio_input = not midi
        self.is_foldable = False
        self.is_frozen = False
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


class Song:
    def __init__(self):
        self.tracks = [Track(), Track(False)]
        self.tempo = 120.0
        self.signature_numerator = 4
        self.signature_denominator = 4
        self.is_playing = False
        self.record_mode = False
        self.session_record = False
        self.undo_depth = 0
        self.undo_count = 0

    def begin_undo_step(self):
        self.undo_depth += 1
        self.undo_count += 1

    def end_undo_step(self):
        self.undo_depth -= 1


def make_api():
    from remote_script.AbletonArrangementMCP.api import ArrangementAPI
    song = Song()
    return ArrangementAPI(song, "12.fake", SimpleNamespace), song
