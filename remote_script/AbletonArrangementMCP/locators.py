"""Conservative adapter for Live 12's grid-snapped, toggle-only cue API."""
from .api import BridgeError, number
from .timeline import near


def create_locator(api, name, time):
    song = api.song
    target = number(time, 'time', high=song.song_length)

    def result(cue):
        if name:
            cue.name = str(name)
        return {'success': True, 'time': cue.time, 'name': cue.name}

    existing = next((c for c in song.cue_points if abs(c.time-target) < 1e-3), None)
    if existing is not None:
        return api._mutate(lambda: result(existing))

    def require_empty():
        # Live can snap to another cue and DELETE it, even when
        # is_cue_point_selected() is false. No public grid read/set API exists.
        if song.cue_points:
            raise BridgeError('UNSUPPORTED', 'Live may delete an existing locator when its cue command snaps to the editing grid. Create additional locators in Live; this tool can rename an existing locator or create the first one only')

    require_empty()
    if song.is_playing or song.record_mode or song.session_record:
        raise BridgeError('NOT_EDITABLE', 'Stop playback/recording before creating a locator')

    def apply():
        original_time = song.current_song_time
        try:
            song.current_song_time = float(target)
            yield  # The native cue command otherwise sees the previous playhead.
            if song.is_playing or song.record_mode or song.session_record or not near(song.current_song_time, target):
                raise BridgeError('STATE_CHANGED', 'Playhead changed before cue creation; no cue created')
            require_empty()  # Also reject a UI-created cue during the deferred tick.
            song.set_or_delete_cue()
            cues = list(song.cue_points)
            if len(cues) != 1:
                raise BridgeError('RESULT_UNCERTAIN', 'New cue was not uniquely identified; inspect locators before retrying')
            output = result(cues[0])
            output['requested_time'] = target
            output['quantized'] = not near(cues[0].time, target)
        finally:
            if not song.is_playing and near(song.current_song_time, target):
                song.current_song_time = original_time
        yield  # Let the restored playhead reach Live before returning success.
        return output

    return api._mutate(apply)
