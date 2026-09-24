# 54개 MCP 도구

원본 37개는 이름·입력 schema·반환 규약을 유지합니다. 기존 원본 도구에 대한
[호환 범위와 데이터셋 설정](compatibility.md)을 함께 확인하세요.

## 원본 도구 37개

| 도구 | 입력 시그니처 (ctx는 MCP가 주입) |
| --- | --- |
| `set_dataset_consent` | `ctx: Context, consent: bool, user_said: str=''` |
| `get_session_info` | `ctx: Context, user_prompt: str=''` |
| `get_remote_script_info` | `ctx: Context, user_prompt: str=''` |
| `get_track_info` | `ctx: Context, track_index: int, user_prompt: str=''` |
| `get_clip_notes` | `ctx: Context, track_index: int, clip_index: int, user_prompt: str=''` |
| `get_device_parameters` | `ctx: Context, track_index: int, device_index: int, user_prompt: str=''` |
| `set_device_parameter` | `ctx: Context, track_index: int, device_index: int, parameter_index: int, value: float, user_prompt: str=''` |
| `get_session_snapshot` | `ctx: Context, include_notes: bool=True, include_params: bool=True, user_prompt: str=''` |
| `create_midi_track` | `ctx: Context, index: int=-1, user_prompt: str=''` |
| `create_audio_track` | `ctx: Context, index: int=-1, user_prompt: str=''` |
| `set_track_name` | `ctx: Context, track_index: int, name: str, user_prompt: str=''` |
| `create_clip` | `ctx: Context, track_index: int, clip_index: int, length: float=4.0, user_prompt: str=''` |
| `create_audio_clip` | `ctx: Context, track_index: int, clip_index: int, path: str, user_prompt: str=''` |
| `add_notes_to_clip` | `ctx: Context, track_index: int, clip_index: int, notes: List[Dict[str, Union[int, float, bool]]], user_prompt: str=''` |
| `clear_notes_from_clip` | `ctx: Context, track_index: int, clip_index: int, user_prompt: str=''` |
| `set_clip_name` | `ctx: Context, track_index: int, clip_index: int, name: str, user_prompt: str=''` |
| `set_arrangement_clip_name` | `ctx: Context, track_index: int, clip_index: int, name: str, user_prompt: str=''` |
| `set_tempo` | `ctx: Context, tempo: float, user_prompt: str=''` |
| `load_instrument_or_effect` | `ctx: Context, track_index: int, uri: str, user_prompt: str=''` |
| `fire_clip` | `ctx: Context, track_index: int, clip_index: int, user_prompt: str=''` |
| `stop_clip` | `ctx: Context, track_index: int, clip_index: int, user_prompt: str=''` |
| `delete_clip` | `ctx: Context, track_index: int, clip_index: int, user_prompt: str=''` |
| `start_playback` | `ctx: Context, user_prompt: str=''` |
| `stop_playback` | `ctx: Context, user_prompt: str=''` |
| `get_browser_tree` | `ctx: Context, category_type: str='all', user_prompt: str=''` |
| `get_browser_items_at_path` | `ctx: Context, path: str, user_prompt: str=''` |
| `load_drum_kit` | `ctx: Context, track_index: int, rack_uri: str, kit_path: str, user_prompt: str=''` |
| `switch_to_arrangement_view` | `ctx: Context, user_prompt: str=''` |
| `set_arrangement_time` | `ctx: Context, time: float, user_prompt: str=''` |
| `get_arrangement_clips` | `ctx: Context, track_index: int, user_prompt: str=''` |
| `duplicate_to_arrangement` | `ctx: Context, track_index: int, clip_index: int, destination_time: float, user_prompt: str=''` |
| `create_locator` | `ctx: Context, name: str, time: float, user_prompt: str=''` |
| `submit_intent` | `ctx: Context, text: str, level: int=5, user_prompt: str=''` |
| `rate_last_action` | `ctx: Context, rating: str, tags: str='', note: str='', user_prompt: str=''` |
| `prefer_candidate` | `ctx: Context, candidate_a: str, candidate_b: str, winner: str, reason: str='', user_prompt: str=''` |
| `reject_last_action` | `ctx: Context, reason: str='', user_prompt: str=''` |
| `record_audition` | `ctx: Context, uri: str, kept: bool=False, search_query: str='', dwell_ms: float=0.0, user_prompt: str=''` |

`create_locator`의 입력 schema는 동일하지만 0.3.1에서 보호 조건이 추가됐습니다.
요청 시간(허용 오차 0.001 beat)에 기존 Locator가 있으면 이름을 바꿉니다. 아무 Locator도
없을 때만 첫 항목을 생성하며, 실제 위치는 Arrangement 그리드에 스냅될 수 있습니다.
이미 다른 Locator가 있으면 추가 생성을 `UNSUPPORTED`로 거부합니다. Live의 toggle
명령이 기존 항목을 삭제하는 문제 때문입니다. 재생/녹음 중 첫 생성도 거부합니다.
추가 Locator는 Live에서 직접 생성하세요.

## 추가 Arrangement 도구 17개

| 도구 | 설명 |
| --- | --- |
| `ableton_status` | Read bridge connectivity, native Live version, tempo, meter and available bridge methods. |
| `ableton_list_tracks` | List normal tracks and their opaque track_id handles, types and native API capabilities. |
| `ableton_list_arrangement_clips` | List a track's Arrangement clips. Return stable clip_id handles and song start/end in beats. |
| `ableton_get_arrangement_clip` | Inspect the current state of an Arrangement clip using a previously listed clip_id. |
| `ableton_update_arrangement_clip` | Set name, RGB color (nearest Live palette color), or muted. Does not move/resize the clip. |
| `ableton_create_arrangement_midi_clip` | Create an empty MIDI Arrangement clip on an existing MIDI track. Refuse overlapping clips. |
| `ableton_create_arrangement_audio_clip` | Import an existing absolute audio file on the Live PC at/after the track's LAST clip. Length depends on Live warp settings. |
| `ableton_duplicate_arrangement_clip` | Duplicate a MIDI/audio Arrangement clip on the SAME track at a free song position in beats. |
| `ableton_copy_arrangement_clip` | Copy to a matching MIDI/audio target track at a free position; preserve the original and return the new clip_id. |
| `ableton_trim_arrangement_clip` | Keep an absolute song-beat range inside the original; return clips[] with new IDs. |
| `ableton_resize_arrangement_clip` | Change either/both boundaries while preserving the content timeline. Looped extension returns up to 64 contiguous native segments. |
| `ableton_move_arrangement_clip` | Verified native copy then source deletion. Optional target_track_id selects a matching track; return a NEW clip_id. Free destination required. |
| `ableton_delete_arrangement_clip` | Delete the identified Arrangement clip from the current Set. Destructive; grouped for Live Undo. |
| `ableton_get_midi_notes` | Read MIDI notes whose onset is in a clip-local beat range; narrow the range if truncated. |
| `ableton_add_midi_notes` | Add 1-256 notes without replacing existing notes. start_time is clip-local beats; pitch is MIDI 0-127. |
| `ableton_update_midi_notes` | Update notes by note_id from ableton_get_midi_notes; omit unchanged fields. Fails if any ID is stale. |
| `ableton_delete_midi_notes` | Delete specific MIDI notes by current note_id, preserving all other notes. Fails if any ID is stale. |

## 선택과 시간 단위

원본 도구의 index는 0부터 시작합니다. 트랙·클립 추가/삭제 후 목록을 다시 조회하세요.
추가 도구의 ID는 현재 Live 연결에서 받은 값만 사용합니다. Set/스크립트 재시작 또는
오래된 handle 제거 후에는 다시 조회해야 합니다. 배열 순서가 바뀌어도 handle은 같은
객체를 가리키며, 삭제된 대상의 ID는 STALE_HANDLE로 거부합니다.

Arrangement beat 0은 1.1.1, 4/4 기준 beat 4는 두 번째 마디입니다. 노트 start_time은
클립 내부 beat이며 Arrangement 타임라인 시작값을 더하지 않습니다. 오디오의 loop
marker 단위는 warping에 따라 seconds일 수 있고 snapshot에 clip_time_unit을 표시합니다.

## 호출 예

아래 ID는 자리표시자입니다. 첫 조회에서 실제 값을 받은 다음 대입합니다.

```text
get_session_info {}
create_midi_track {"index": -1}
create_clip {"track_index": 2, "clip_index": 0, "length": 4}
get_track_info {"track_index": 2}

ableton_list_tracks {}
ableton_list_arrangement_clips {"track_id": "<track_id>"}
ableton_create_arrangement_midi_clip {"track_id": "<track_id>", "start_beats": 16, "length_beats": 4}
ableton_add_midi_notes {"clip_id": "<clip_id>", "notes": [{"pitch": 60, "start_time": 0, "duration": 1, "velocity": 100}]}
ableton_get_midi_notes {"clip_id": "<clip_id>", "start_beats": 0, "length_beats": 4}
ableton_update_midi_notes {"clip_id": "<clip_id>", "notes": [{"note_id": 1, "pitch": 64}]}
ableton_delete_midi_notes {"clip_id": "<clip_id>", "note_ids": [1]}
ableton_move_arrangement_clip {"clip_id": "<clip_id>", "destination_beats": 24}
ableton_create_arrangement_audio_clip {"track_id": "<audio_track_id>", "file_path": "D:/Samples/kick.wav", "start_beats": 32}
```

원본 get_* 출력은 JSON 문자열 또는 사람이 읽는 문자열입니다. 확장 도구는 JSON
객체를 반환합니다. `ableton_move_arrangement_clip`이 반환하는 새 clip_id를 이후
호출에 사용하세요. 노트 ID도 실제 조회 결과를 사용해야 합니다. 트리밍·리사이즈는
`clips[]`, `changed`, `warnings`를 반환하며 새 ID 전체를 확인해야 합니다.
[새 도구의 인수·예시·편집 의미·복구](timeline-editing.md)를 참고하세요.

## 확장 도구의 제한과 실패

- 이름 최대 256자, RGB 0..0xFFFFFF (Live가 가장 가까운 색으로 맞춤).
- 생성·복제·복사·이동은 대상 트랙의 기존 클립과 겹침을 거부. 이동 시 자기 원본과 겹쳐도 거부.
- 오디오 가져오기는 해당 Live PC의 실제 파일을 읽으며 트랙 마지막 클립 이후만 허용.
- MIDI 추가·수정·삭제는 한 번에 1..256개, 노트 조회는 최대 1,000개.
  잘린 결과는 start_beats/length_beats 범위를 나눠 조회합니다.
- Freeze·녹음 중 확장 편집을 거부하며 native capability가 없으면 UNSUPPORTED.
- move는 복제→검증→원본 삭제를 한 Undo 단계에 묶음. native 호출이 트랜잭션은
  아니므로 PARTIAL_MOVE/RESULT_UNCERTAIN 또는 timeout이면 목록을 다시 확인합니다.
- 즉시 자동 재시도하거나 전체 Set을 자동 Undo/저장하지 않습니다.
- trim/resize는 요청 범위가 다른 클립과 겹치면 거부. 루프 확장은 최대 64개 결과.
  Unwarped audio 파일 경계 초과는 거부. 오디오 trim은 설치된 silence.wav가 필요.
- PARTIAL_EDIT는 원본 교체 중 실패이며 복구용 음소거 복사본이 남을 수 있음.
- Take Lane/Comping/오토메이션 직접 편집과 자동 Set 저장은 미제공.
