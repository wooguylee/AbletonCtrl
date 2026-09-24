import importlib.util
import math
import unittest
from fakes import Clip, make_api


class APITests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("remote_script"),
                             "Arrangement bridge has not been implemented")
        self.api, self.song = make_api()
        self.track_id = self.api.call("list_tracks", {})["tracks"][0]["track_id"]
        self.clip_id = self.api.call("list_clips", {"track_id": self.track_id})["clips"][0]["clip_id"]

    def assert_error(self, code, method, params):
        from remote_script.AbletonArrangementMCP.api import BridgeError
        with self.assertRaises(BridgeError) as ctx:
            self.api.call(method, params)
        self.assertEqual(ctx.exception.code, code)

    def test_status_and_pagination(self):
        status = self.api.call("status", {})
        self.assertEqual(status["live_version"], "12.fake")
        self.assertEqual(status["time_unit"], "beats")
        self.assertEqual(self.api.call("list_tracks", {"offset": 1, "limit": 1})["total"], 2)

    def test_handle_survives_reorder_but_rejects_deleted_clip(self):
        original = self.song.tracks[0].arrangement_clips[0]
        self.song.tracks[0].arrangement_clips.insert(0, Clip(8))
        self.api.call("update_clip", {"clip_id": self.clip_id, "name": "선택한 클립"})
        self.assertEqual(original.name, "선택한 클립")
        self.song.tracks[0].arrangement_clips.remove(original)
        self.assert_error("STALE_HANDLE", "delete_clip", {"clip_id": self.clip_id})

    def test_removed_track_invalidates_clip(self):
        self.song.tracks.pop(0)
        self.assert_error("STALE_HANDLE", "get_clip", {"clip_id": self.clip_id})

    def test_create_duplicate_delete_and_undo(self):
        created = self.api.call("create_midi_clip", {"track_id": self.track_id, "start_beats": 4, "length_beats": 8})
        self.assertEqual(created["start_beats"], 4)
        copied = self.api.call("duplicate_clip", {"clip_id": created["clip_id"], "destination_beats": 12})
        self.assertEqual(copied["end_beats"], 20)
        self.api.call("delete_clip", {"clip_id": copied["clip_id"]})
        self.assert_error("STALE_HANDLE", "get_clip", {"clip_id": copied["clip_id"]})
        self.assertEqual(self.song.undo_count, 3)
        self.assertEqual(self.song.undo_depth, 0)

    def test_overlap_rejected_without_changing_set(self):
        self.assert_error("OVERLAP", "create_midi_clip", {"track_id": self.track_id, "start_beats": 2, "length_beats": 4})
        self.assert_error("OVERLAP", "duplicate_clip", {"clip_id": self.clip_id, "destination_beats": 1})
        self.assertEqual(len(self.song.tracks[0].arrangement_clips), 1)
        self.assertEqual(self.song.undo_count, 0)

    def test_invalid_numbers_and_unknown_fields_rejected(self):
        for value in [math.nan, math.inf, -1, True, "4"]:
            self.assert_error("INVALID_ARGUMENT", "create_midi_clip", {"track_id": self.track_id, "start_beats": value, "length_beats": 4})
        self.assert_error("INVALID_ARGUMENT", "update_clip", {"clip_id": self.clip_id, "name": "changed", "color": -1})
        self.assertEqual(self.song.tracks[0].arrangement_clips[0].name, "Test clip")
        self.assert_error("INVALID_ARGUMENT", "update_clip", {"clip_id": self.clip_id, "start_time": 8})
        self.assert_error("UNKNOWN_METHOD", "eval", {"code": "bad"})

    def test_frozen_recording_and_wrong_type(self):
        self.song.tracks[0].is_frozen = True
        self.assert_error("NOT_EDITABLE", "delete_clip", {"clip_id": self.clip_id})
        self.song.tracks[0].is_frozen = False
        self.song.record_mode = True
        self.assert_error("NOT_EDITABLE", "update_clip", {"clip_id": self.clip_id, "muted": True})
        self.song.record_mode = False
        audio_id = self.api.call("list_tracks", {})["tracks"][1]["track_id"]
        self.assert_error("WRONG_TRACK_TYPE", "create_midi_clip", {"track_id": audio_id, "start_beats": 4, "length_beats": 4})

    def test_notes_use_clip_time_and_midi_spec_objects(self):
        self.api.call("add_notes", {"clip_id": self.clip_id, "notes": [{"pitch": 127, "start_time": 0, "duration": 1, "velocity": 100}]})
        notes = self.api.call("get_notes", {"clip_id": self.clip_id, "start_beats": 0, "length_beats": 4})["notes"]
        self.assertEqual(notes[0]["pitch"], 127)
        self.assertEqual(notes[0]["start_time"], 0)
        self.assert_error("INVALID_ARGUMENT", "add_notes", {"clip_id": self.clip_id, "notes": [{"pitch": 60, "duration": 0, "start_time": 0}]})
        self.assertEqual(len(notes), 1)

    def test_native_error_closes_undo_step(self):
        def fail(clip):
            raise RuntimeError("native error")
        self.song.tracks[0].delete_clip = fail
        self.assert_error("LIVE_ERROR", "delete_clip", {"clip_id": self.clip_id})
        self.assertEqual(self.song.undo_depth, 0)

    def test_missing_capability_is_explicit(self):
        self.song.tracks[0].create_midi_clip = None
        self.assert_error("UNSUPPORTED", "create_midi_clip", {"track_id": self.track_id, "start_beats": 4, "length_beats": 4})


if __name__ == "__main__":
    unittest.main()
