import tempfile
import unittest
from pathlib import Path
from copy import deepcopy
from fakes import Clip, Track, ClipSlot, make_api
from remote_script.AbletonArrangementMCP.api import BridgeError


class TimelineTests(unittest.TestCase):
    def setUp(self):
        self.api, self.song = make_api()
        self.track = self.song.tracks[0]
        self.source = self.track.arrangement_clips[0]
        self.source.start_time, self.source.end_time = 8, 12
        self.source.loop_start, self.source.loop_end = 2, 6
        self.source.start_marker, self.source.end_marker = 2, 10
        self.clip_id = self.api._handle('clip', self.source, self.track)

    def invoke(self, method, **params):
        self.assertIn(method, self.api.METHODS, 'Requested timeline operation is not implemented')
        return self.api.call(method, dict(clip_id=self.clip_id, **params))

    def assert_range(self, result, start, end):
        clips = result['clips']
        self.assertAlmostEqual(clips[0]['start_beats'], start)
        self.assertAlmostEqual(clips[-1]['end_beats'], end)
        for left, right in zip(clips, clips[1:]):
            self.assertAlmostEqual(left['end_beats'], right['start_beats'])
        self.assertEqual(self.song.undo_depth, 0)

    def test_copy_across_tracks_preserves_original_and_native_payload(self):
        target = Track()
        target.arrangement_clips = []
        self.song.tracks.append(target)
        self.source.custom_envelope = [0.1, 0.8]
        result = self.invoke('copy_clip', target_track_id=self.api._handle('track', target), destination_beats=8)
        self.assertEqual(result['track_id'], self.api._handle('track', target))
        self.assertIn(self.source, self.track.arrangement_clips)
        self.assertEqual(target.arrangement_clips[0].custom_envelope, [0.1, 0.8])

    def test_copy_rejects_type_mismatch_and_occupied_target(self):
        audio = self.song.tracks[1]
        with self.assertRaisesRegex(BridgeError, 'type'):
            self.invoke('copy_clip', target_track_id=self.api._handle('track', audio), destination_beats=8)
        with self.assertRaisesRegex(BridgeError, 'overlap'):
            self.invoke('copy_clip', target_track_id=self.api._handle('track', self.track), destination_beats=8)
        self.assertEqual(self.song.undo_count, 0)

    def test_audio_copy_and_cross_track_move(self):
        audio_source = self.song.tracks[1]
        destination = Track(False)
        destination.arrangement_clips = []
        self.song.tracks.append(destination)
        handle = self.api._handle('clip', audio_source.arrangement_clips[0], audio_source)
        target = self.api._handle('track', destination)
        copy = self.api.call('copy_clip', {'clip_id': handle, 'target_track_id': target, 'destination_beats': 4})
        moved = self.api.call('move_clip', {'clip_id': handle, 'target_track_id': target, 'destination_beats': 8})
        self.assertEqual(copy['type'], 'audio')
        self.assertEqual(moved['track_id'], target)
        self.assertEqual(len(audio_source.arrangement_clips), 0)
        self.assertEqual(len(destination.arrangement_clips), 2)

    def test_frozen_and_recording_targets_rejected_before_writes(self):
        self.track.is_frozen = True
        with self.assertRaisesRegex(BridgeError, 'unfreeze'):
            self.invoke('trim_clip', start_beats=9, end_beats=11)
        self.track.is_frozen = False
        self.song.record_mode = True
        with self.assertRaisesRegex(BridgeError, 'recording'):
            self.invoke('resize_clip', end_beats=16)
        self.assertEqual(self.song.undo_count, 0)

    def test_loop_segment_limit_and_tiny_positive_range(self):
        self.source.looping = True
        with self.assertRaisesRegex(BridgeError, '64'):
            self.invoke('resize_clip', end_beats=1000)
        self.assertIn(self.source, self.track.arrangement_clips)
        result = self.invoke('resize_clip', start_beats=20, end_beats=20.00001)
        self.assertTrue(result['clips'])
        self.assert_range(result, 20, 20.00001)

    def test_staging_duplicate_wrong_length_cleans_owned_copy(self):
        duplicate = self.track.duplicate_clip_to_arrangement
        def wrong_length(clip, position):
            duplicate(clip, position)
            self.track.arrangement_clips[-1].end_time += 1
        self.track.duplicate_clip_to_arrangement = wrong_length
        with self.assertRaisesRegex(BridgeError, 'bounds/length'):
            self.invoke('trim_clip', start_beats=9, end_beats=11)
        self.assertEqual(self.track.arrangement_clips, [self.source])

    def test_original_delete_failure_keeps_source_and_backup(self):
        delete = self.track.delete_clip
        def fail(clip):
            if clip == self.source:
                raise RuntimeError('cannot delete original')
            return delete(clip)
        self.track.delete_clip = fail
        with self.assertRaisesRegex(BridgeError, 'backup'):
            self.invoke('trim_clip', start_beats=9, end_beats=11)
        self.assertIn(self.source, self.track.arrangement_clips)
        self.assertTrue(any(c != self.source and c.end_time-c.start_time == 4 for c in self.track.arrangement_clips))

    def test_trim_both_edges_preserves_neighbors_and_content(self):
        before, after = Clip(4, 4), Clip(12, 4)
        self.track.arrangement_clips.extend([before, after])
        result = self.invoke('trim_clip', start_beats=9, end_beats=11)
        self.assert_range(result, 9, 11)
        self.assertIn(before, self.track.arrangement_clips)
        self.assertIn(after, self.track.arrangement_clips)
        self.assertEqual(len(self.track.arrangement_clips), 3)
        edited = next(c for c in self.track.arrangement_clips if c.start_time == 9)
        self.assertEqual(edited.start_marker, 3)
        self.assertFalse(edited.muted)

    def test_resize_unlooped_exposes_hidden_content_both_sides(self):
        result = self.invoke('resize_clip', start_beats=7, end_beats=15)
        self.assert_range(result, 7, 15)
        self.assertEqual(len(self.track.arrangement_clips), 1)
        self.assertEqual(self.track.arrangement_clips[0].loop_start, 1)
        self.assertEqual(self.track.arrangement_clips[0].loop_end, 9)
        self.assertEqual(self.song.undo_count, 1)

    def test_holding_area_stays_beyond_the_entire_requested_expansion(self):
        for looped in (False, True):
            with self.subTest(looped=looped):
                self.setUp()
                self.source.looping = looped
                result = self.invoke('resize_clip', end_beats=80)
                self.assert_range(result, 8, 80)
                self.assertEqual(len(self.track.arrangement_clips), len(result['clips']))
                self.assertTrue(all(not c.muted for c in self.track.arrangement_clips))

    def test_resize_looped_retains_phase_across_partial_cycle(self):
        self.source.looping = True
        self.source.loop_start, self.source.loop_end = 0, 3
        self.source.start_marker = 1
        result = self.invoke('resize_clip', start_beats=7, end_beats=19)
        self.assert_range(result, 7, 19)
        self.assertGreater(len(result['clips']), 1)
        for clip in self.track.arrangement_clips:
            expected = (1 + clip.start_time - 8) % 3
            self.assertAlmostEqual(clip.start_marker % 3, expected)
            self.assertTrue(clip.looping)

    def test_loop_intro_is_played_before_wrapping_into_loop(self):
        self.source.looping = True
        self.source.start_marker = 0
        self.source.loop_start, self.source.loop_end = 8, 12
        result = self.invoke('resize_clip', end_beats=24)
        self.assert_range(result, 8, 24)
        placed = sorted(self.track.arrangement_clips, key=lambda c: c.start_time)
        self.assertEqual([c.start_marker for c in placed], [0, 4, 8, 8])

    def test_invalid_trim_and_expansion_overlap_do_not_write(self):
        with self.assertRaisesRegex(BridgeError, 'inside'):
            self.invoke('trim_clip', start_beats=7, end_beats=12)
        self.track.arrangement_clips.append(Clip(12, 4))
        with self.assertRaisesRegex(BridgeError, 'overlap'):
            self.invoke('resize_clip', end_beats=14)
        self.assertEqual(self.song.undo_count, 0)

    def test_noop_and_ignored_native_resize(self):
        result = self.invoke('resize_clip', start_beats=8, end_beats=12)
        self.assert_range(result, 8, 12)
        self.assertEqual(self.song.undo_count, 0)
        self.source.ignore_resize = True
        with self.assertRaisesRegex(BridgeError, 'length|bounds'):
            self.invoke('resize_clip', end_beats=16)
        self.assertIn(self.source, self.track.arrangement_clips)
        self.assertEqual((self.source.start_time, self.source.end_time), (8, 12))

    def test_final_placement_failure_retains_full_backup(self):
        duplicate = self.track.duplicate_clip_to_arrangement
        def fail(clip, position):
            if position == 9:
                raise RuntimeError('destination rejected')
            return duplicate(clip, position)
        self.track.duplicate_clip_to_arrangement = fail
        with self.assertRaisesRegex(BridgeError, 'PARTIAL|backup|recovery'):
            self.invoke('trim_clip', start_beats=9, end_beats=11)
        self.assertTrue(any(c.end_time-c.start_time == 4 for c in self.track.arrangement_clips))
        self.assertEqual(self.song.undo_depth, 0)

    def test_audio_trim_and_unwarped_resize_units(self):
        self.track = self.song.tracks[1]
        self.source = self.track.arrangement_clips[0]
        self.source.start_time, self.source.end_time = 8, 12
        self.source.loop_start, self.source.loop_end = 1, 3
        self.source.start_marker, self.source.end_marker = 1, 10
        self.source.seconds_per_beat = 0.5
        self.source.sample_length, self.source.sample_rate = 100, 10
        self.clip_id = self.api._handle('clip', self.source, self.track)
        with tempfile.TemporaryDirectory() as directory:
            self.api.silence_path = str(Path(directory, 'silence.wav'))
            Path(self.api.silence_path).write_bytes(b'fake audio')
            result = self.invoke('trim_clip', start_beats=9, end_beats=11)
            self.assert_range(result, 9, 11)
            self.clip_id = result['clips'][0]['clip_id']
            result = self.invoke('resize_clip', end_beats=13)
            self.assert_range(result, 9, 13)
            self.assertTrue(all(not s.has_clip for s in self.track.clip_slots))

    def test_unwarped_file_boundary_and_missing_silence_preserve_source(self):
        track = self.song.tracks[1]
        clip = track.arrangement_clips[0]
        clip.loop_start, clip.loop_end = 0, 2
        clip.sample_length, clip.sample_rate = 20, 10
        handle = self.api._handle('clip', clip, track)
        with self.assertRaisesRegex(BridgeError, 'file boundary'):
            self.api.call('resize_clip', {'clip_id': handle, 'end_beats': 12})
        with self.assertRaisesRegex(BridgeError, 'silence.wav'):
            self.api.call('trim_clip', {'clip_id': handle, 'start_beats': 1, 'end_beats': 3})
        self.assertEqual(track.arrangement_clips, [clip])

    def test_unwarped_resize_waits_for_live_tick_before_replacing_original(self):
        from remote_script.AbletonArrangementMCP.deferred import Deferred
        track = self.song.tracks[1]
        source = track.arrangement_clips[0]
        source.loop_start, source.loop_end = 1, 3
        source.sample_length, source.sample_rate = 100, 10
        source.ignore_resize = True  # Live 12.4.6 applies unwarped length next tick.
        handle = self.api._handle('clip', source, track)
        pending = self.api.call('resize_clip', {'clip_id': handle, 'end_beats': 6})
        self.assertIsInstance(pending, Deferred)
        self.assertIn(source, track.arrangement_clips)
        self.assertEqual(self.song.undo_depth, 1)
        for clip in track.arrangement_clips:
            if clip is not source:
                clip.end_time = clip.start_time + (clip.loop_end-clip.loop_start)/0.5
        result = pending.advance()
        self.assert_range(result, 0, 6)
        self.assertNotIn(source, track.arrangement_clips)
        self.assertEqual(len(track.arrangement_clips), 1)

    def test_midi_trim_does_not_read_audio_only_native_properties(self):
        from unittest.mock import patch
        def audio_only(clip):
            raise RuntimeError('Gain is only available for Audio Clips')
        with patch.object(type(self.source), 'gain', property(audio_only), create=True):
            result = self.invoke('trim_clip', start_beats=9, end_beats=11)
        self.assert_range(result, 9, 11)

    def test_deferred_resize_with_envelopes_preserves_source(self):
        track = self.song.tracks[1]
        source = track.arrangement_clips[0]
        source.loop_start, source.loop_end = 1, 3
        source.sample_length, source.sample_rate = 100, 10
        source.ignore_resize, source.has_envelopes = True, True
        with self.assertRaisesRegex(BridgeError, 'with clip envelopes'):
            self.api.call('resize_clip', {'clip_id': self.api._handle('clip', source, track), 'end_beats': 6})
        self.assertEqual(track.arrangement_clips, [source])
        self.assertEqual(self.song.undo_depth, 0)

    def test_cancel_deferred_resize_cleans_staging_and_closes_undo(self):
        from remote_script.AbletonArrangementMCP.deferred import Deferred
        track = self.song.tracks[1]
        source = track.arrangement_clips[0]
        source.loop_start, source.loop_end = 1, 3
        source.sample_length, source.sample_rate = 100, 10
        source.ignore_resize = True
        pending = self.api.call('resize_clip', {'clip_id': self.api._handle('clip', source, track), 'end_beats': 6})
        self.assertIsInstance(pending, Deferred)
        pending.close()
        self.assertEqual(track.arrangement_clips, [source])
        self.assertEqual(self.song.undo_depth, 0)

    def test_source_gain_change_during_deferred_resize_is_preserved(self):
        track = self.song.tracks[1]
        source = track.arrangement_clips[0]
        source.loop_start, source.loop_end = 1, 3
        source.sample_length, source.sample_rate = 100, 10
        source.ignore_resize, source.gain = True, 0.5
        pending = self.api.call('resize_clip', {'clip_id': self.api._handle('clip', source, track), 'end_beats': 6})
        source.gain = 0.75
        for clip in track.arrangement_clips:
            if clip is not source:
                clip.end_time = clip.start_time + (clip.loop_end-clip.loop_start)/0.5
        with self.assertRaisesRegex(BridgeError, 'Source changed'):
            pending.advance()
        self.assertEqual(track.arrangement_clips, [source])
        self.assertEqual(source.gain, 0.75)
        self.assertEqual(self.song.undo_depth, 0)

    def test_wrong_length_audio_cover_is_cleaned_before_failure(self):
        track = self.song.tracks[1]
        source = track.arrangement_clips[0]
        handle = self.api._handle('clip', source, track)
        duplicate = track.duplicate_clip_to_arrangement
        def wrong_cover(clip, position):
            duplicate(clip, position)
            if not clip.is_arrangement_clip:
                track.arrangement_clips[-1].end_time += 1
        track.duplicate_clip_to_arrangement = wrong_cover
        with tempfile.TemporaryDirectory() as directory:
            self.api.silence_path = str(Path(directory, 'silence.wav'))
            Path(self.api.silence_path).write_bytes(b'fake audio')
            with self.assertRaisesRegex(BridgeError, 'bounds/length'):
                self.api.call('trim_clip', {'clip_id': handle, 'start_beats': 1, 'end_beats': 3})
        self.assertEqual(track.arrangement_clips, [source])
        self.assertTrue(all(not s.has_clip for s in track.clip_slots))

    def test_audio_trim_with_full_session_restores_scene_and_existing_clips(self):
        track = self.song.tracks[1]
        source = track.arrangement_clips[0]
        handle = self.api._handle('clip', source, track)
        self.song.scenes = [object(), object()]
        original_scenes = list(self.song.scenes)
        for t in self.song.tracks:
            for slot in t.clip_slots:
                slot.create_clip(4)
        original_clips = [[s.clip for s in t.clip_slots] for t in self.song.tracks]
        def create(index):
            self.assertEqual(index, -1)
            self.song.scenes.append(object())
            for t in self.song.tracks:
                t.clip_slots.append(ClipSlot())
        def delete(index):
            del self.song.scenes[index]
            for t in self.song.tracks:
                del t.clip_slots[index]
        self.song.create_scene, self.song.delete_scene = create, delete
        with tempfile.TemporaryDirectory() as directory:
            self.api.silence_path = str(Path(directory, 'silence.wav'))
            Path(self.api.silence_path).write_bytes(b'fake audio')
            result = self.api.call('trim_clip', {'clip_id': handle, 'start_beats': 1, 'end_beats': 3})
        self.assert_range(result, 1, 3)
        self.assertEqual(self.song.scenes, original_scenes)
        self.assertEqual([[s.clip for s in t.clip_slots] for t in self.song.tracks], original_clips)


if __name__ == '__main__':
    unittest.main()
