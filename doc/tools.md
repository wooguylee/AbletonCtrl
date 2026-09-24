# MCP 도구 사용법

## 좌표와 식별자

- Arrangement 시간은 **4분음표 기준 beat**입니다. `0`은 곡의 `1.1.1` 위치입니다.
- 4/4에서 1마디는 4 beats, 5마디 시작은 16 beats입니다. 다른 박자는
  `분자 × 4 / 분모`로 마디 길이를 계산합니다. 박자 변경이 있으면 구간별로 계산해야 합니다.
- MIDI 노트 `start_time`은 **클립 내부 좌표**입니다. Arrangement 시작 위치를 더해서
  노트를 넣으면 안 됩니다. 루프·클립 시작 오프셋은 별도로 고려합니다.
- `track_id`, `clip_id`는 목록에서 반환된 문자열을 그대로 사용합니다. 이름이나
  트랙 번호로 만들 수 없습니다. Bridge 재시작, Set 변경, 삭제, 캐시 퇴출 후 재조회합니다.
- 목록의 `index`는 표시용 0 기반 순서입니다. 편집 대상은 항상 식별자로 전달합니다.

## 10개 도구

| MCP 이름 | 주요 입력 | 동작 |
| --- | --- | --- |
| `ableton_status` | 없음 | Live 버전, 템포·박자·재생 상태 |
| `ableton_list_tracks` | `offset=0`, `limit=100` | 일반 트랙 목록·식별자·API capability |
| `ableton_list_arrangement_clips` | `track_id`, 페이지 | 해당 트랙의 Arrangement 클립 목록 |
| `ableton_get_arrangement_clip` | `clip_id` | 현재 클립 상태 |
| `ableton_update_arrangement_clip` | `clip_id`, `name?`, `color?`, `muted?` | 지정한 속성만 수정 |
| `ableton_create_arrangement_midi_clip` | `track_id`, `start_beats`, `length_beats` | 빈 MIDI 클립 생성 |
| `ableton_duplicate_arrangement_clip` | `clip_id`, `destination_beats` | 같은 트랙의 빈 위치에 복제 |
| `ableton_delete_arrangement_clip` | `clip_id` | 지정 클립 삭제 |
| `ableton_get_midi_notes` | `clip_id`, `start_beats=0`, `length_beats=16`, `limit=1000` | 시작 시점이 범위 안인 노트 조회 |
| `ableton_add_midi_notes` | `clip_id`, `notes` | 기존 노트를 유지하면서 1~256개 추가 |

목록은 페이지당 최대 100개입니다. `total`과 `offset`을 확인하여 다음 페이지를
읽습니다. 노트는 최대 1,000개를 반환하며 `truncated=true`이면 조회 시간 범위를
좁힙니다. 기본 노트 범위가 클립 전체를 의미하지는 않습니다.

`color`는 정수 RGB `0xRRGGBB` (0~16777215)이며 실제 Live 팔레트에서 가까운 색상이
적용됩니다. `muted=true`는 클립 비활성화입니다. 오디오 클립의 내부 loop 좌표는
Warp 상태에 따라 초 또는 beat이므로 `clip_time_unit`을 함께 확인하세요.

## 예: 빈 MIDI 클립에 4개 음표 추가

1. `ableton_status`로 연결을 확인합니다.
2. `ableton_list_tracks`로 MIDI 트랙의 `track_id`를 얻습니다.
3. `ableton_list_arrangement_clips`로 빈 구간을 확인합니다.
4. 다음 인자로 `ableton_create_arrangement_midi_clip`을 호출합니다.

```json
{"track_id":"목록에서 받은 track_id", "start_beats":16, "length_beats":4}
```

5. 생성 결과의 `clip_id`로 `ableton_add_midi_notes`를 호출합니다.

```json
{
  "clip_id":"생성 결과의 clip_id",
  "notes":[
    {"pitch":60,"start_time":0,"duration":0.5,"velocity":100},
    {"pitch":64,"start_time":1,"duration":0.5,"velocity":100},
    {"pitch":67,"start_time":2,"duration":0.5,"velocity":100},
    {"pitch":72,"start_time":3,"duration":0.5,"velocity":100}
  ]
}
```

6. 이름은 `ableton_update_arrangement_clip`의 `name`으로 바꿉니다.
7. `ableton_get_midi_notes`와 클립 상세를 다시 읽어 결과를 확인합니다.

자연어 예: “Arrangement의 MIDI 트랙 목록을 확인하고, 첫 트랙의 5마디가 비어 있으면
한 마디 클립을 만든 뒤 C-E-G-C 음표를 한 박자 간격으로 넣어줘.”
실제 도구 호출은 위 식별자를 조회한 뒤 수행됩니다.

## 편집 결과와 제한

생성·복제의 `[start, end)` 구간이 기존 클립과 겹치면 거부합니다. 경계가 맞닿는
구간은 허용됩니다. 녹음 모드나 Session 녹음이 켜져 있거나 트랙이 Freeze이면
쓰기 작업을 거부합니다. 읽기는 계속 가능합니다.

각 쓰기는 Live Undo 단계로 묶지만 **트랜잭션은 아닙니다.** Live가 중간 속성 변경
이후 오류를 내면 일부 변경이 남을 수 있습니다. 자동 Undo나 자동 재시도는 하지
않습니다. 오류 뒤에는 현재 상태를 확인하고 필요하면 Live에서 Undo하세요.
MCP 결과는 메모리상의 Set 변경이며 파일 저장 완료를 의미하지 않습니다.
