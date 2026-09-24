import tempfile
import unittest
from pathlib import Path
from fakes import Clip, make_api


class ExtendedArrangementTests(unittest.TestCase):
    def setUp(self):
        self.api, self.song = make_api()
        self.track = self.api.call("list_tracks", {})["tracks"][0]["track_id"]
        self.clip = self.api.call("list_clips", {"track_id": self.track})["clips"][0]["clip_id"]

    def test_move_preserves_source_until_copy_confirmed(self):
        self.assertIn("move_clip", self.api.METHODS)
        result = self.api.call("move_clip", {"clip_id": self.clip, "destination_beats": 8})
        self.assertEqual(result["start_beats"], 8)
        self.assertEqual(len(self.song.tracks[0].arrangement_clips), 1)
        self.assertEqual(self.song.undo_count, 1)

    def test_failed_move_delete_reports_both_clips(self):
        self.assertIn("move_clip", self.api.METHODS)
        from remote_script.AbletonArrangementMCP.api import BridgeError
        def fail(clip):
            raise RuntimeError("delete failed")
        self.song.tracks[0].delete_clip = fail
        with self.assertRaisesRegex(BridgeError, "original.*copy"):
            self.api.call("move_clip", {"clip_id": self.clip, "destination_beats": 8})
        self.assertEqual(len(self.song.tracks[0].arrangement_clips), 2)
        self.assertEqual(self.song.undo_depth, 0)

    def test_audio_import_requires_free_tail_and_audio_track(self):
        self.assertIn("create_audio_clip", self.api.METHODS)
        from remote_script.AbletonArrangementMCP.api import BridgeError
        audio = self.api.call("list_tracks", {})["tracks"][1]["track_id"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "test.wav")
            path.write_bytes(b"fake file; decoding belongs to Live")
            self.song.tracks[1].arrangement_clips.append(Clip(12, 4, midi=False))
            with self.assertRaisesRegex(BridgeError, "last clip"):
                self.api.call("create_audio_clip", {"track_id": audio, "start_beats": 4, "file_path": str(path)})
            result = self.api.call("create_audio_clip", {"track_id": audio, "start_beats": 16, "file_path": str(path)})
            self.assertEqual(result["type"], "audio")

    def test_note_id_update_delete_and_stale_id_rejection(self):
        self.assertIn("update_notes", self.api.METHODS)
        from remote_script.AbletonArrangementMCP.api import BridgeError
        self.api.call("add_notes", {"clip_id": self.clip, "notes": [{"pitch": 60, "start_time": 0, "duration": 1}]})
        self.api.call("update_notes", {"clip_id": self.clip, "notes": [{"note_id": 1, "pitch": 64, "velocity": 90}]})
        self.assertEqual(self.api.call("get_notes", {"clip_id": self.clip})["notes"][0]["pitch"], 64)
        with self.assertRaisesRegex(BridgeError, "note IDs"):
            self.api.call("delete_notes", {"clip_id": self.clip, "note_ids": [1, 999]})
        self.assertEqual(len(self.song.tracks[0].arrangement_clips[0].notes), 1)
        self.api.call("delete_notes", {"clip_id": self.clip, "note_ids": [1]})
        self.assertEqual(self.api.call("get_notes", {"clip_id": self.clip})["notes"], [])


if __name__ == "__main__":
    unittest.main()
