import unittest
from types import SimpleNamespace
from fakes import make_api


class LocatorTests(unittest.TestCase):
    def test_deferred_playhead_creates_exact_cue_and_restores_state(self):
        from remote_script.AbletonArrangementMCP.locators import create_locator
        from remote_script.AbletonArrangementMCP.deferred import Deferred
        api, song = make_api()
        song.song_length = 100
        song.start_time = 16
        song.clip_trigger_quantization = 4
        song.current_song_time = 16
        # Cue creation sees Live's committed clock, not the latest setter value.
        clock = [16]
        song.set_or_delete_cue = lambda: song.cue_points.append(SimpleNamespace(time=clock[0], name=''))
        song.is_cue_point_selected = lambda: False
        pending = create_locator(api, 'Test cue', 0.25)
        self.assertIsInstance(pending, Deferred)
        self.assertEqual(song.cue_points, [])
        for _ in range(6):
            clock[0] = song.current_song_time
            pending = pending.advance()
            if not isinstance(pending, Deferred):
                break
        self.assertEqual(pending['time'], 0.25)
        self.assertEqual(song.cue_points[0].name, 'Test cue')
        self.assertEqual(song.current_song_time, 16)
        self.assertEqual(song.clip_trigger_quantization, 4)
        self.assertEqual(song.undo_depth, 0)

    def test_existing_cue_is_renamed_without_toggle(self):
        from remote_script.AbletonArrangementMCP.locators import create_locator
        api, song = make_api()
        song.song_length = 100
        song.start_time = 16
        song.clip_trigger_quantization = 4
        song.cue_points = [SimpleNamespace(time=4.0005, name='Old')]
        result = create_locator(api, 'New', 4)
        self.assertEqual(result['name'], 'New')
        self.assertEqual(len(song.cue_points), 1)

    def test_cancel_restores_clock_quantization_and_undo(self):
        from remote_script.AbletonArrangementMCP.locators import create_locator
        api, song = make_api()
        song.song_length = 100
        song.start_time = 16
        song.clip_trigger_quantization = 4
        song.current_song_time = 16
        pending = create_locator(api, 'Test', 8)
        pending.close()
        self.assertEqual(song.current_song_time, 16)
        self.assertEqual(song.clip_trigger_quantization, 4)
        self.assertEqual(song.cue_points, [])
        self.assertEqual(song.undo_depth, 0)

    def test_user_clock_change_is_not_rewound_on_failure(self):
        from remote_script.AbletonArrangementMCP.locators import create_locator
        from remote_script.AbletonArrangementMCP.api import BridgeError
        api, song = make_api()
        song.song_length = 100
        song.start_time = 16
        song.clip_trigger_quantization = 4
        pending = create_locator(api, 'Test', 8)
        song.current_song_time = 32
        song.is_playing = True
        with self.assertRaisesRegex(BridgeError, 'Playhead changed'):
            pending.advance()
        self.assertEqual(song.current_song_time, 32)
        self.assertEqual(song.undo_depth, 0)

    def test_new_cue_with_existing_locators_is_rejected_before_writes(self):
        from remote_script.AbletonArrangementMCP.locators import create_locator
        from remote_script.AbletonArrangementMCP.api import BridgeError
        api, song = make_api()
        song.song_length = 100
        song.current_song_time = 16
        song.cue_points = [SimpleNamespace(time=8, name='Keep')]
        song.is_cue_point_selected = lambda: False
        song.set_or_delete_cue = lambda: self.fail('Must not toggle an occupied snapped cue')
        with self.assertRaisesRegex(BridgeError, 'may delete'):
            create_locator(api, 'New', 6)
        self.assertEqual(song.current_song_time, 16)
        self.assertEqual(song.cue_points[0].name, 'Keep')
        self.assertEqual(song.undo_depth, 0)

    def test_cue_added_during_yield_is_preserved(self):
        from remote_script.AbletonArrangementMCP.locators import create_locator
        from remote_script.AbletonArrangementMCP.api import BridgeError
        api, song = make_api()
        song.song_length = 100
        song.current_song_time = 16
        pending = create_locator(api, 'New', 6)
        song.cue_points = [SimpleNamespace(time=8, name='User cue')]
        song.set_or_delete_cue = lambda: self.fail('Must preserve concurrent UI cue')
        with self.assertRaisesRegex(BridgeError, 'may delete'):
            pending.advance()
        self.assertEqual(song.cue_points[0].name, 'User cue')
        self.assertEqual(song.undo_depth, 0)
