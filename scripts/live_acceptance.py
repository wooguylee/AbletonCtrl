"""Opt-in real Live acceptance through MCP stdio. Creates named test tracks.

Use a disposable Set. No automatic retries, Set saving, or track deletion.
Raw reports and generated test media are kept under the project's doc/local/.
"""
import argparse
import asyncio
import datetime
import json
import math
import struct
import sys
import uuid
import wave
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]


def tone(path):
    with wave.open(str(path), 'wb') as out:
        out.setparams((1, 2, 22050, 0, 'NONE', 'not compressed'))
        out.writeframes(b''.join(struct.pack('<h', int(1000 * math.sin(2*math.pi*220*i/22050)))
                                 for i in range(22050 * 8)))


def bounds(result, start, end):
    clips = result.get('clips', [result])
    assert clips and math.isclose(clips[0]['start_beats'], start, abs_tol=1e-4), result
    assert math.isclose(clips[-1]['end_beats'], end, abs_tol=1e-4), result
    for a, b in zip(clips, clips[1:]):
        assert math.isclose(a['end_beats'], b['start_beats'], abs_tol=1e-4), result


async def run(args):
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    local = ROOT / 'doc/local'
    local.mkdir(parents=True, exist_ok=True)
    report_path = local / ('live-acceptance-' + stamp + '.json')
    report = {'started': stamp, 'calls': [], 'checks': [], 'test_tracks': [], 'complete': False}
    params = StdioServerParameters(command=sys.executable,
        args=['-m', 'ableton_arrangement_mcp', '--config', str(args.config.resolve())])
    try:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listing = await session.list_tools()
                report['advertised_tools'] = [t.name for t in listing.tools]
                assert len(listing.tools) == 54

                async def call(name, arguments=None, expect_error=False):
                    result = await session.call_tool(name, arguments or {})
                    data = result.structuredContent
                    if data is None:
                        data = {'text': '\n'.join(getattr(c, 'text', '') for c in result.content)}
                    raw = data.get('result') if not name.startswith('ableton_') else None
                    if isinstance(raw, str):
                        try:
                            data = json.loads(raw)
                        except ValueError:
                            data = raw
                    failed = bool(result.isError) or (isinstance(data, dict) and bool(data.get('error'))) or (isinstance(data, str) and
                             (data.lower().startswith('error') or any(word in data.lower() for word in ('failed to', 'no loadable'))))
                    record = {'tool': name, 'arguments': arguments or {}, 'data': data,
                              'is_error': failed, 'expected_error': expect_error}
                    report['calls'].append(record)
                    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
                    print(name + (' EXPECTED ERROR' if failed and expect_error else ' ERROR' if failed else ' OK'), flush=True)
                    if failed != expect_error:
                        raise AssertionError(record)
                    return data

                async def check(label, action):
                    await action()
                    report['checks'].append(label)
                    print('PASS ' + label, flush=True)

                status = await call('ableton_status')
                report['live_version'] = status['live_version']
                await call('get_remote_script_info')
                original = await call('get_session_info')
                await call('ableton_list_tracks')
                if not args.run_writes:
                    report['complete'] = True
                    return report_path
                assert not original['is_playing'], 'Stop Live before running acceptance'
                token = uuid.uuid4().hex[:6]
                tracks = []
                for kind in ('midi', 'midi', 'midi', 'audio', 'audio'):
                    index = (await call('ableton_status'))['track_count']
                    await call('create_' + kind + '_track', {'index': -1})
                    name = 'MCPTEST ' + token + ' ' + kind + ' ' + str(index)
                    await call('set_track_name', {'track_index': index, 'name': name})
                    report['test_tracks'].append(name)
                    tracks.append(next(t for t in (await call('ableton_list_tracks'))['tracks'] if t['name'] == name))
                m, dest, drums, audio, audio_dest = tracks
                wav = local / ('acceptance-' + token + '.wav')
                tone(wav)
                try:
                    async def legacy():
                        idx = m['index']
                        slot = {'track_index': idx, 'clip_index': 0}
                        await call('get_track_info', {'track_index': idx})
                        await call('create_clip', dict(slot, length=8))
                        await call('set_clip_name', dict(slot, name='MCP Session test'))
                        notes = [{'pitch': 60, 'start_time': 0, 'duration': 1, 'velocity': 25}]
                        await call('add_notes_to_clip', dict(slot, notes=notes))
                        assert (await call('get_clip_notes', slot))['note_count'] == 1
                        await call('fire_clip', slot)
                        await call('stop_clip', slot)
                        await call('stop_playback')
                        await call('duplicate_to_arrangement', dict(slot, destination_time=8))
                        assert (await call('get_arrangement_clips', {'track_index': idx}))['clip_count'] == 1
                        await call('set_arrangement_clip_name', {'track_index': idx, 'clip_index': 0, 'name': 'MCP native Session copy'})
                        await call('clear_notes_from_clip', slot)
                        assert (await call('get_clip_notes', slot))['note_count'] == 0
                        await call('delete_clip', slot)
                        a_slot = {'track_index': audio['index'], 'clip_index': 0}
                        await call('create_audio_clip', dict(a_slot, path=str(wav)))
                        await call('delete_clip', a_slot)
                        await call('set_tempo', {'tempo': original['tempo'] + 1})
                        assert (await call('ableton_status'))['tempo'] == original['tempo'] + 1
                        await call('set_tempo', {'tempo': original['tempo']})
                        await call('set_arrangement_time', {'time': 4})
                        await call('start_playback')
                        assert (await call('ableton_status'))['is_playing']
                        await call('stop_playback')
                        await call('switch_to_arrangement_view')
                        # Only rename our prior test cue. Never rename a user's locator.
                        snap = await call('get_session_snapshot', {'include_notes': True, 'include_params': True})
                        owned = next((c for c in snap['cue_points'] if c['name'].startswith('MCPTEST ')), None)
                        assert owned or not snap['cue_points'], 'Use a disposable Set with no user locators'
                        cue = owned['time'] if owned else 4
                        await call('create_locator', {'name': 'MCPTEST ' + token, 'time': cue})
                        actual = await call('get_session_snapshot', {'include_notes': False, 'include_params': False})
                        assert any(c['name'] == 'MCPTEST ' + token and math.isclose(c['time'], cue, abs_tol=1e-3) for c in actual['cue_points']), actual['cue_points']
                    await check('original Session/transport/Arrangement tools', legacy)

                    async def arrangement():
                        track = m['track_id']
                        x = await call('ableton_create_arrangement_midi_clip', {'track_id': track, 'start_beats': 32, 'length_beats': 8})
                        x = await call('ableton_update_arrangement_clip', {'clip_id': x['clip_id'], 'name': 'MCP MIDI lifecycle', 'color': 0x00FF00, 'muted': True})
                        assert x['name'] == 'MCP MIDI lifecycle' and x['muted']
                        await call('ableton_add_midi_notes', {'clip_id': x['clip_id'], 'notes': [
                            {'pitch': 60, 'start_time': 0, 'duration': 1, 'velocity': 40},
                            {'pitch': 67, 'start_time': 3, 'duration': 2, 'velocity': 50}]})
                        ns = (await call('ableton_get_midi_notes', {'clip_id': x['clip_id']}))['notes']
                        await call('ableton_update_midi_notes', {'clip_id': x['clip_id'], 'notes': [{'note_id': ns[0]['note_id'], 'pitch': 62}]})
                        assert (await call('ableton_get_midi_notes', {'clip_id': x['clip_id']}))['notes'][0]['pitch'] == 62
                        await call('ableton_delete_midi_notes', {'clip_id': x['clip_id'], 'note_ids': [ns[1]['note_id']]})
                        assert len((await call('ableton_get_midi_notes', {'clip_id': x['clip_id']}))['notes']) == 1
                        duplicate = await call('ableton_duplicate_arrangement_clip', {'clip_id': x['clip_id'], 'destination_beats': 48})
                        await call('ableton_delete_arrangement_clip', {'clip_id': duplicate['clip_id']})
                        await call('ableton_get_arrangement_clip', {'clip_id': duplicate['clip_id']}, expect_error=True)
                        copied = await call('ableton_copy_arrangement_clip', {'clip_id': x['clip_id'], 'target_track_id': dest['track_id'], 'destination_beats': 32})
                        assert (await call('ableton_get_arrangement_clip', {'clip_id': x['clip_id']}))['start_beats'] == 32
                        moved = await call('ableton_move_arrangement_clip', {'clip_id': copied['clip_id'], 'destination_beats': 64, 'target_track_id': track})
                        bounds(moved, 64, 72)
                        trimmed = await call('ableton_trim_arrangement_clip', {'clip_id': moved['clip_id'], 'start_beats': 65, 'end_beats': 70})
                        bounds(trimmed, 65, 70)
                        expanded = await call('ableton_resize_arrangement_clip', {'clip_id': trimmed['clips'][0]['clip_id'], 'start_beats': 64, 'end_beats': 80})
                        bounds(expanded, 64, 80)
                        assert all(c['muted'] for c in expanded['clips'])
                        await call('ableton_copy_arrangement_clip', {'clip_id': x['clip_id'], 'target_track_id': audio['track_id'], 'destination_beats': 0}, expect_error=True)
                        await call('ableton_duplicate_arrangement_clip', {'clip_id': x['clip_id'], 'destination_beats': 33}, expect_error=True)
                        a = await call('ableton_create_arrangement_audio_clip', {'track_id': audio['track_id'], 'file_path': str(wav), 'start_beats': 16})
                        length = a['duration_beats']
                        assert length > 4
                        a = await call('ableton_copy_arrangement_clip', {'clip_id': a['clip_id'], 'target_track_id': audio_dest['track_id'], 'destination_beats': 16})
                        a = await call('ableton_move_arrangement_clip', {'clip_id': a['clip_id'], 'destination_beats': 64, 'target_track_id': audio['track_id']})
                        r = await call('ableton_trim_arrangement_clip', {'clip_id': a['clip_id'], 'start_beats': 65, 'end_beats': 64+length-1})
                        bounds(r, 65, 64+length-1)
                        endpoint = 64+length if a['clip_time_unit'] == 'seconds' else 64+length+2
                        r = await call('ableton_resize_arrangement_clip', {'clip_id': r['clips'][0]['clip_id'], 'start_beats': 64, 'end_beats': endpoint})
                        bounds(r, 64, endpoint)
                        if a['clip_time_unit'] == 'seconds':
                            await call('ableton_resize_arrangement_clip', {'clip_id': r['clips'][0]['clip_id'], 'end_beats': endpoint+2}, expect_error=True)
                        await call('ableton_list_arrangement_clips', {'track_id': audio['track_id']})
                    await check('Arrangement MIDI/audio lifecycle, cross-track copy/move, trim/resize and guards', arrangement)

                    async def browser():
                        tree = await call('get_browser_tree', {'category_type': 'all'})
                        assert 'Instruments' in str(tree)
                        synths = await call('get_browser_items_at_path', {'path': 'instruments'})
                        drift = next(c for c in synths['items'] if c['name'] == 'Drift')
                        await call('load_instrument_or_effect', {'track_index': dest['index'], 'uri': drift['uri']})
                        dev = await call('get_device_parameters', {'track_index': dest['index'], 'device_index': 0})
                        pars = dev['device']['parameters']
                        p = next(p for p in pars if p.get('is_enabled', True) and not p.get('is_quantized', False) and p['max'] > p['min'])
                        value = p['min'] + (p['max']-p['min'])*0.37
                        args = {'track_index': dest['index'], 'device_index': 0, 'parameter_index': p['index']}
                        await call('set_device_parameter', dict(args, value=value))
                        actual = (await call('get_device_parameters', {'track_index': dest['index'], 'device_index': 0}))['device']['parameters'][p['index']]['value']
                        assert math.isclose(actual, value, rel_tol=1e-5, abs_tol=1e-5)
                        await call('set_device_parameter', dict(args, value=p['value']))
                        rack = next(c for c in synths['items'] if c['name'] == 'Drum Rack')
                        await call('load_drum_kit', {'track_index': drums['index'], 'rack_uri': rack['uri'], 'kit_path': args_kit_path})
                        loaded = await call('get_track_info', {'track_index': drums['index']})
                        assert any(d['class_name'] == 'DrumGroupDevice' and d['name'] != 'Drum Rack' for d in loaded['devices']), loaded
                    args_kit_path = args.kit_path
                    await check('browser, instrument, device parameter and drum kit', browser)

                    async def disabled_dataset():
                        await call('set_dataset_consent', {'consent': False, 'user_said': 'Automated local test; no collection consent.'})
                        result = await call('submit_intent', {'text': 'Synthetic acceptance test'})
                        assert 'off' in str(result).lower(), result
                        await call('rate_last_action', {'rating': 'thumbs_up'})
                        await call('prefer_candidate', {'candidate_a': 'test-a', 'candidate_b': 'test-b', 'winner': 'test-a'})
                        await call('reject_last_action', {'reason': 'Synthetic acceptance test'})
                        await call('record_audition', {'uri': 'test:local-only', 'kept': False})
                    await check('optional dataset tools remain disabled', disabled_dataset)
                    used = {c['tool'] for c in report['calls']}
                    assert set(report['advertised_tools']) <= used, set(report['advertised_tools']) - used
                    report['complete'] = True
                finally:
                    await call('stop_playback')
                    await call('set_tempo', {'tempo': original['tempo']})
                    await call('set_arrangement_time', {'time': original['current_song_time']})
    except Exception as exc:
        report['complete'] = False
        report['failure'] = str(exc)
        raise
    finally:
        report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
        print('Report: ' + str(report_path), flush=True)
    return report_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT/'doc/local/bridge.json')
    parser.add_argument('--run-writes', action='store_true', help='Authorize test track/clip/device creation in the open disposable Set')
    parser.add_argument('--kit-path', default='packs/Core Library/Racks/Drum Racks/Drum Machines', help='Installed browser folder containing a loadable kit')
    asyncio.run(run(parser.parse_args()))
