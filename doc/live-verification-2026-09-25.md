# Live 12.4.6 Suite 실기 검증 — 2026-09-25 / 0.3.1

사용자가 AbletonVVoori 설정 완료 후 전체 테스트와 Arrangement 필수 검증을 요청했다.
Windows에서 실제 MCP stdio → 인증 TCP → Live main thread 경로로 검증했다.
원본 37개와 확장 17개 도구를 모두 호출하되, 데이터셋 6개는 수집 꺼짐 동작만 확인했다.
**최종 실행:** `live-acceptance-20260925-010206.json`, 54개 도구 / 93회 호출 /
예상 오류 3회 / 모든 시나리오 통과. 마지막 Warp Off 트림·확장과 최초 4개 트랙의
내용 불변도 최종 설치본으로 다시 확인했다.

**모든 도구 호출 확인은 모든 입력 조합/Live 버전의 보장을 뜻하지 않는다.**

## Arrangement 필수 결과

| 시나리오 | 결과 |
| --- | --- |
| MIDI 생성·조회·이름/색상/음소거·노트 추가/ID 수정/삭제 | 통과 |
| MIDI 같은/다른 트랙 복사·이동·삭제, 원본·노트 유지 | 통과 |
| Looped MIDI [8,16] → trim [9,14] → resize [8,20] | 4개 연속 결과 구간; 저장된 Set의 StartRelative로 loop phase 확인 |
| Warped looping audio [16,32] → [18,28] → [17,30] | 3개 연속 결과 구간 |
| Unlooped MIDI [64,72] → [66,70] → [65,74] | 경계·마커 확인 |
| Unlooped Warp On audio [64,80] → [66,76] → [65,78] | 경계·마커 확인 |
| Unlooped Warp Off audio [128,144] → [130,140] → [129,142] → [128,144] | 지연 길이 갱신 수정 후 통과; seconds 마커 0..8 복원 |
| Warp Off 오디오 다른 트랙 복사 [300,316] → [301,313] → [300,316] | 통과; 실제 결과 조회 |
| Warp Off 음원 끝 초과 [128,145] 요청 | CONTENT_BOUNDARY, 원본 및 트랙 클립 목록 유지 |
| 점유 구간 복사·MIDI를 audio 트랙에 복사·삭제된 ID 사용 | 예상 오류; 다른 클립 덮어쓰기 없음 |
| 오디오 트랙 Session 8슬롯 모두 점유한 상태의 trim | 임시 9번째 Scene 추가/정리; 모든 트랙 기존 Session 슬롯과 Scene 목록 동일 |
| MIDI move UI Undo/Redo | 각 한 단계로 원본/이동 결과 확인 |
| Warp Off 지연 resize UI Undo/Redo | 각 두 단계 관찰; 첫 Undo의 음소거 임시 클립은 두 번째 Undo에서 정리 |

루프 위상은 일부 MIDI 구간의 native Set XML을 읽기 전용으로 비교했다. 오디오를
렌더링하여 파형 전체가 같다는 검사나 모든 envelope의 보존 검증은 수행하지 않았다.

## 발견한 오류와 수정

1. **Warp Off 길이 갱신 지연:** marker setter 직후 length가 이전 값이라 정상 resize를
   실패로 처리했다. generator continuation으로 다음 Live tick을 기다리고 검증한다.
   main thread만 사용하며, 대기 중 원본은 보존하고 다른 MCP 실행은 직렬화한다.
2. **원본 상태 변경 보호:** 지연 후 위치·마커·gain·pitch·tempo 등을 다시 검사한다.
   MIDI에서 gain을 읽으면 native RuntimeError가 나므로 audio 속성은 audio만 검사한다.
   기존 clip envelope가 있는 지연 resize는 거부한다. UI를 함께 편집하지 않아야 한다.
3. **Locator 생성 API:** current_song_time 변경 직후 cue 명령이 이전 위치를 사용할 수
   있다. tick을 기다리도록 수정했다. 그리드 스냅이 다른 Locator를 삭제하는 현상도
   재현했으며, selected 판정/global quantization으로 막을 수 없었다. **기존 항목 이름
   변경과 첫 생성만 허용한다. 추가 생성은 Live에서 직접 해야 한다.** 첫 생성 실제 위치는
   스냅될 수 있으며 반환 값을 확인한다. 생성 직전에도 cue 목록을 다시 검사한다.
4. **Undo 단계:** 지연 작업은 여러 Undo 단계에 걸칠 수 있다. 실기에서는 두 단계였다.
   응답/실패 안내에 이를 명시했다. 자동 Undo나 무조건 재시도는 하지 않는다.

원본 vendor 코드와 37개 입력 schema는 변경하지 않았고, Locator 보호는 통합 surface의
adapter에서 처리한다. 첫 Locator 생성·기존 항목 이름 변경·추가 생성 거부를 실기로 확인했다.

## 다른 기능과 검증 범위

Session MIDI/audio 생성·이름·노트·fire/stop/delete, 트랙 생성/이름/조회, 재생/정지·템포,
Arrangement View/시간, Session→Arrangement 복사, snapshot을 실행했다. Browser 조회,
Drift 로딩·파라미터 변경/복원, Core Library의 **505 Core Kit** 로딩 후 장치도 재조회했다.
선택적 데이터셋은 꺼짐 응답을 확인했으며 외부 업로드·인증은 시험하지 않았다.

처음 있던 빈 MIDI 2/audio 2 트랙의 정보·Session 슬롯·Arrangement는 최초 snapshot과
비교했다. 테스트 자료는 별도 Set `doc/local/AbletonCtrl-Acceptance Project/`에 보존한다.
테스트용 ACTEST/MCPTEST 트랙은 검사할 수 있게 남긴다. Live는 정지 상태로 둔다.

## 다른 PC에서 재실행

설치 및 Live 활성화를 마치고, **별도 빈 Set/사본**에서 재생·녹음을 멈춘다.
Drift와 Core Library Drum Machines가 설치되어 있어야 전체 쓰기 검사가 통과한다.
테스트 중 UI나 다른 제어기로 Set을 수정하지 않는다.

```powershell
.venv\Scripts\python scripts\live_acceptance.py
.venv\Scripts\python scripts\live_acceptance.py --run-writes
```

첫 명령은 연결/도구목록 및 읽기 4회만 수행한다. 두 번째는 트랙 5개, MIDI/audio 클립,
장치, Locator를 만들며 잠시 재생하고 마지막에 정지·tempo/time 복원을 시도한다.
반복 실행은 테스트 트랙을 추가한다. 자동 Set 저장/트랙 삭제는 하지 않는다.
기존 Locator가 있으면 MCPTEST 이름의 테스트 Locator만 재사용하고, 사용자 Locator만
있는 Set은 사용하지 않는다. Kit 경로가 다르면 `--kit-path`로 실제 Browser 경로를 준다.
기본 `doc/local/bridge.json` 대신 `--config`를 지정할 수 있다.

각 호출·예상 오류·체크 결과는 `doc/local/live-acceptance-*.json`에 남는다.
작업이 실패하면 보고서와 현재 상태를 먼저 확인한다. 무조건 재실행하지 않는다.

## 로컬 증거와 미검증 범위

원시 로그·Set·미디어는 doc/local에만 남고 Git에는 넣지 않는다.

- `live-probe-log.jsonl`: 개별 native 시나리오 호출/응답 및 디버깅 실패 기록.
- `unwarped-boundaries.json`, `full-slots-result.json`: 파일 경계/다른 트랙/Session 보존.
- `undo-move.json`, `undo-resize.json`: UI Undo/Redo 전후 조회.
- `locator-final.json`: 첫 Locator 및 추가 생성 거부의 항목 보존.
- `live-before-tests.json`, `live-final-original-tracks.json`: 최초/최종 4개 트랙 비교.
- `final-unwarped.json`: 최종 설치본 Warp Off 트림·리사이즈 재확인.
- `latest-tests.txt`, `wheel-verify.txt`: 자동 회귀·별도 wheel 환경 검사.

자동 테스트 61개(타임라인 24개), 원본 schema/vendor hash 검사, Python 3.7 native 문법,
설치본 소스 hash parity, pip check, compileall, 독립 venv wheel 설치/54개 발견을 확인했다.
macOS, 타 Live 버전, 제3자 플러그인, 모든 음원 포맷, tempo automation, 기존 clip envelope
내용 보존, comping/freeze의 실제 UI, 모든 녹음 상태 조합과 optional backend upload는 미검증이다.
보호 분기의 일부는 fake 기반 자동 테스트로만 검증했다.
