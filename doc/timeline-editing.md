# 타임라인 트리밍·리사이즈와 트랙 간 복사 — 0.3.0

이전 미지원 표시는 구현 범위를 제한한 것이었습니다. 공개 LOM의 Arrangement
`start_time`/`end_time`은 읽기 속성이어서 단순 대입으로 끝낼 수 없지만, native 복제·
마커 수정·가장자리 겹침을 조합하는 방법이 있습니다. 이번 버전은 이 경로를 구현합니다.
공식 API와 구현 보고의 차이는 [조사 기록](research.md)에 남겼습니다.

## 도구와 입력

모든 시간은 **곡의 절대 quarter-note beats**입니다. 4/4에서 beat 0은 1.1.1,
beat 4는 2.1.1입니다. 먼저 트랙·클립 목록에서 현재 ID를 받습니다.

| 도구 | 인수 | 결과 |
| --- | --- | --- |
| `ableton_copy_arrangement_clip` | `clip_id`, `target_track_id`, `destination_beats` | 복사본 snapshot, 새 `clip_id`; 원본 유지 |
| `ableton_move_arrangement_clip` | `clip_id`, `destination_beats`, 선택 `target_track_id` | 새 `clip_id`; 대상 생략 시 같은 트랙 |
| `ableton_trim_arrangement_clip` | `clip_id`, `start_beats`, `end_beats` | 원본 내부 구간만 남김. `clips[]`, `changed`, `warnings` |
| `ableton_resize_arrangement_clip` | `clip_id`, 선택 `start_beats`, 선택 `end_beats` | 생략한 경계는 유지. 축소·확장. `clips[]`, `changed`, `warnings` |

복사·이동은 MIDI→MIDI, 오디오→오디오 일반 트랙에 허용합니다. 같은 트랙에도 복사할
수 있습니다. 복제·이동 대상은 원본을 포함한 기존 클립과 겹치면 거부합니다.
리사이즈는 교체 대상 원본과 겹칠 수 있으나 다른 클립을 덮어쓰지는 않습니다.
Freeze·녹음 상태는 편집 전에 거부합니다.

```text
ableton_list_tracks {}
ableton_list_arrangement_clips {"track_id": "<source_track_id>"}
ableton_copy_arrangement_clip {"clip_id": "<source_clip_id>", "target_track_id": "<matching_track_id>", "destination_beats": 32}
ableton_trim_arrangement_clip {"clip_id": "<copy_id_at_32_to_40>", "start_beats": 34, "end_beats": 38}
ableton_resize_arrangement_clip {"clip_id": "<trim_result_clips_0_id>", "end_beats": 42}
```

예시는 원본 길이가 8 beat일 때의 순서입니다. 자리표시자는 실제 결과 ID로 바꾸세요.
트리밍·리사이즈는 원본을 교체하므로 다음 작업에 이전 ID를 재사용하지 않습니다.
루프 확장은 여러 클립을 만들 수 있어 `clips[0]`만 처리하면 전체 결과를 놓칩니다.
변경할 경계가 동일하면 `changed: false`로 기존 클립을 반환합니다.

## 편집 의미

트리밍은 지정 구간 밖을 보이지 않게 자릅니다. 원본 노트/오디오를 새로 작성하거나
원본 오디오 파일을 재가져오지 않고 Live의 native 복사 내용을 사용합니다.
리사이즈도 타임 스트레칭이 아닙니다. 원래 곡 위치에 대응하는 콘텐츠가 이어집니다.

- 루프가 꺼진 MIDI/warped audio: 보이지 않던 앞·뒤 콘텐츠를 마커로 노출합니다.
  존재하지 않는 MIDI 구간은 비어 있으며 warped audio는 파일 바깥에 무음이 생길 수
  있습니다. 실제 길이와 마커를 읽어 요청값과 일치하는지 확인합니다.
- Unwarped audio: 현재 클립의 관찰된 seconds/beat 비율로 마커를 계산합니다.
  음원 시작 이전이나 파일 끝 이후는 거부합니다. 템포 자동화에 따른 구간별 비율 차이는
  아직 지원/검증하지 않았으며, 복사된 길이가 달라지면 성공으로 반환하지 않습니다.
- 루프가 켜진 클립 확장: 기존 구간과 확장 구간을 연속된 native 복사본으로 구성합니다.
  시작 마커로 루프 위상을 맞추고 루프 앞의 일회성 도입부도 보존하도록 계산합니다.
  **하나의 길어진 클립으로 합치지 않습니다.** 호출당 최대 64개이며, 초과하면 쓰기 전
  거부합니다. 더 짧은 범위로 나누거나 결과를 Live에서 수동 Consolidate할 수 있습니다.

## 내부 처리와 복구

`timeline.py`의 `TimelineEditor`가 모든 처리에 사용됩니다. 임시 위치는 현재 모든
트랙의 콘텐츠, 재생 위치, **요청한 전체 끝 위치**보다 뒤로 잡습니다. 임시 복사본은
음소거하고, 원본을 지우기 전에 준비 결과의 실제 경계를 확인합니다.

MIDI 가장자리 트림은 빈 임시 MIDI 클립을, 오디오 트림은 무음 Session 클립을 해당
가장자리에 겹쳐 넣고 제거합니다. 겹침은 소유한 임시 복사본에만 적용합니다.
Arrangement 원본을 점유된 구간으로 직접 복제하지 않습니다. 오디오 보조 소스는
설치 때 생성한 `silence.wav`이며, 빈 Session 슬롯이 없으면 맨 끝에 임시 Scene을
추가했다가 정리합니다. 예상하지 못한 사용자 콘텐츠가 들어간 Scene은 삭제하지 않습니다.
Live가 보조 오디오의 warp/loop 설정을 즉시 적용하지 않으면 명확한 오류로 중단합니다.

준비가 끝나면 전체 원본 백업도 음소거하여 보관하고, 원본을 삭제한 뒤 최종 위치에
검증된 복사본을 배치합니다. 최종 배치가 모두 성공하면 임시 자료와 백업을 제거합니다.
Live의 한 Undo 단계로 묶지만 native 호출 전체가 원자적 트랜잭션은 아닙니다.

| 상태 | 대응 |
| --- | --- |
| 준비 단계 실패 | 원본 유지, 소유한 임시 자료를 정리 시도. 정리 실패 자료는 오류의 복구 ID 및 목록으로 확인 |
| `PARTIAL_EDIT` | 원본 교체 시작 후 실패. 부분 결과와 음소거 백업이 남을 수 있음. 모든 클립을 다시 조회하고 원본 구간·백업을 확인 |
| `PARTIAL_MOVE` | 복사 후 원본 삭제 실패. 오류에 있는 원본·복사본을 확인 |
| `RESULT_UNCERTAIN` / timeout | native 처리 완료 여부나 경계가 확실하지 않음. 즉시 재시도하지 말고 상태 재조회 |

필요하면 Live에서 수동 Undo로 복구합니다. 자동 전체 Undo나 자동 Set 저장은 하지
않습니다. 복구 클립 ID와 위치를 확인한 뒤 삭제/복사 도구로 수동 복구할 수도 있습니다.

## 설치·검증 상태

0.2 사용자는 MCP 패키지와 Remote Script를 함께 0.3으로 업데이트하고 설치 도우미를
`--replace`로 다시 실행해야 합니다. 자세한 명령은 [설치 안내](setup.md)에 있습니다.

Fake native 모델, 실제 TCP/stdio 통합, wheel 설치를 검증했습니다. **실제 Live 12
Suite에서의 트림 이후 객체 identity, 오디오 warp 처리 시점, clip automation/내용
보존·Undo는 아직 확인하지 못했습니다.** 실제 설치 후 별도 Set에서
[실기 점검](verification.md)을 수행해야 합니다. 이 제한을 성공 검증으로 오해하지 마세요.
