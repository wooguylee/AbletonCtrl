# 검증 결과 — AbletonCtrl 0.3.1

2026-09-25 Windows **Live 12.4.6 Suite 실기 테스트**를 수행했습니다.
자동 테스트 **61개** 통과. 최신 native 시나리오·제한·재실행 명령은
[실기 보고서](live-verification-2026-09-25.md)에 있습니다.

아래는 0.3.0 당시의 기록이며, 당시 실기 미수행 상태는 위 보고서로 갱신됐습니다.

## 이전 검증 — 2026-09-24, AbletonCtrl 0.3.0

**자동 테스트 48개 통과, 독립 Python 환경의 wheel 설치 및 54개 MCP 도구 검색 통과.**
실제 Ableton Live 프로세스 안에서의 실행, macOS, 선택적 Supabase 업로드는 검증하지 않았습니다.
현재 PC의 실제 User Library에 설치까지 완료했으며 Control Surface 활성화는 사용자가
진행합니다. 사용자의 Set은 편집하지 않았습니다.

## 실행한 검사

| 검사 | 결과 |
| --- | --- |
| Python / MCP SDK | Windows, Python 3.12.10 / MCP 1.30.0 |
| `python -m unittest discover -s tests -v` | 48 tests, OK (타임라인 19개 포함) |
| `python -m pip check` | No broken requirements found |
| `python -m compileall -q src remote_script scripts tests` | 성공 |
| Live 측 6개 Python 파일의 Python 3.7 문법 파싱 | 성공 (실제 Live 런타임 검증과 별개) |
| 원본 MCP 37개 전체 입력 JSON Schema 비교 | 이름·파라미터·기본값 보존 |
| vendored 16개 파일 SHA256 / 원본 git object 비교 | 고정 commit과 byte 단위 일치; LF checkout 규칙 포함 |
| wheel 제작·별도 venv 설치 | 서버·Live Script·MIT LICENSE 포함 확인 |
| `scripts/verify_wheel.py` | 소스 밖 임시 프로젝트 설치, native hash 일치, PCM 무음 WAV 생성, stdio 54개 검색 성공 |
| 실제 Live 연결 | 최초 `--check`는 BRIDGE_UNAVAILABLE; Live 실기 검증 미수행 |

[test-results.txt](test-results.txt)에 unittest 출력,
[requirements-tested.txt](requirements-tested.txt)에 검증 환경 버전을 기록했습니다.
wheel은 `doc/local/dist/`에 생성되며 배포 소스만 Git에 올립니다.

## 통합 검증 범위

실제 stdio MCP subprocess → 인증 TCP → 통합 ArrangementSurface dispatch → fake Live
객체 순서로 실행했습니다. Live의 원본 handler 코드를 사용하되 native 객체를 모형으로
대체했습니다. 이는 모든 도구를 실제 Live에서 사용했다는 뜻은 아닙니다.

- 원본 Session/트랙 조회·생성·이름, 클립 생성·이름·노트·실행·정지·삭제.
- 원본 장치 파라미터 조회·수정, 재생·정지, Arrangement 시각·목록, 전체 snapshot.
- 동일 연결에서 확장 Arrangement 생성·메타데이터·복제·이동·삭제와 MIDI 추가·수정·삭제.
- 동일 stdio 연결에서 트리밍·리사이즈·트랙 간 복사와 원본 도구의 공존.
- MIDI/오디오 복사·트랙 간 이동, 양쪽 가장자리 트림, 인접 클립 보존,
  unlooped 양끝 확장, 루프 위상·도입부 보존·64개 제한·아주 짧은 결과 구간.
- 요청 끝보다 뒤의 임시 배치, native 길이 변경 무시/불일치, unwarped 파일 경계,
  삭제/최종 배치 실패 시 전체 백업, 임시 커버·Session 슬롯·추가 Scene 정리.
- handle 순서 변경·삭제, note_id 만료, 겹침·녹음·Freeze 거부, 실패 후 Undo 단계 종료.
- 이동 중 원본 삭제 실패 시 복사본/원본 상태와 오류 보고, 오디오 import의 마지막 클립 보호.
- 분할 TCP 프레임·인증·만료·재사용 ID·타임아웃 후 늦은 쓰기 거부·16 MiB 초과 제한.
- Live 접근의 주 스레드 제한, 원본 schedule_message 큐 대기로 인한 교착 방지.
- 설치 실패 시 기존 설정 보존, 업데이트 백업, 다른 프로젝트 venv를 잘못 선택하지 않음.

브라우저/음원/Pack 로딩과 모든 native 메서드의 세부 동작은 아래 실기 점검이 필요합니다.
원본 기능은 source·schema 보존 및 주요 경로 테스트로 확인했고, 특정 PC의 콘텐츠/플러그인
호환성을 보증하지 않습니다.

## 독립 코드 리뷰

0.2 읽기 전용 리뷰의 두 수정과 회귀 검증을 유지했습니다.

1. 선택적 Live UI 수집이 꺼져도 해당 capability를 광고하던 문제: 비활성 상태에서는
   `drain_passive_events`를 광고하지 않아 원본 데이터셋의 오래된 pre-state 재사용 방지.
2. 재사용 대상 프로젝트의 무관한 `.venv`를 선택하던 설치 문제: 실제 패키지가 설치된
   installer의 `sys.executable`을 사용. 회귀 테스트 추가.

리뷰어는 수정 확인 후 열린 코드 차단 항목이 없음을 보고했습니다. 초기 0.1 버전에서
수정한 설치 실패 설정 보존·대화 metadata 처리 회귀 테스트도 계속 통과합니다.

0.3 타임라인 리뷰에서도 세 문제를 재현한 뒤 수정하고 회귀 테스트로 확인했습니다.

1. 긴 확장에서 임시 영역이 최종 영역과 겹침: 전체 요청 끝을 임시 배치 기준에 포함.
2. 루프 앞 도입부가 모듈러 계산으로 건너뛰어짐: 첫 루프 끝 이전의 원래 콘텐츠 위치 유지.
3. 잘못된 길이의 임시 커버가 정리 대상에서 누락: 고유 신규 객체를 먼저 소유 목록에
   넣고 음소거한 뒤 경계를 검증. 오류 시에도 삭제 가능.

리뷰어가 수정된 타임라인 테스트 19개를 별도로 실행해 통과와 남은 코드 차단 사항이
없음을 확인했습니다. Fake의 native 동작 모델은 실기 결과를 대체하지 않습니다.

## Live 12 Suite 실기 확인 절차

새 빈 Set 또는 별도 사본으로 실행합니다. 각 편집 후 화면과 새 조회를 함께 확인합니다.

1. [설치/전환](setup.md) 후 `--check`, `get_remote_script_info`, 0.3.0/54개 도구 확인.
2. 원본 Session: MIDI/오디오 트랙 생성, Session MIDI 클립·노트 생성/조회/삭제,
   이름 변경, fire/stop/delete, Session audio import를 확인합니다.
3. 원본 Browser: 설치된 악기/이펙트/Drum Kit를 검색·로딩하고 파라미터 조회/변경.
   원본 snapshot, Locator, Arrangement view/time, Session→Arrangement 복사도 확인합니다.
4. 확장 MIDI: 빈 구간에 4 beat 클립 생성, 노트 추가·note_id 수정·삭제, 색상·muted 변경.
5. 같은/다른 트랙 복사·이동: 자유 구간에서 위치·길이·노트·loop·clip envelope가 유지되는지 확인하고
   반환된 새 ID로 조회합니다. 원본 삭제 실패 시 자동으로 재시도하지 않습니다.
6. 오디오: MIDI 트랙 오용 거부, 마지막 클립 이후 파일 import, 실제 warp/길이,
   같은 트랙 복제·이동·삭제를 확인합니다. 실제 오디오 포맷 지원은 Live가 결정합니다.
7. 잘린/반복/자동화가 포함된 클립의 복제 내용, Undo/Redo 후 handle 무효화를 확인합니다.
8. 녹음·Freeze·겹침 거부, 모달 창·Set 변경·Live 재시작 후 목록 재조회,
   Control Surface 해제 시 socket 종료를 확인합니다.
9. MIDI와 warped/unwarped audio의 양쪽 트리밍, 한쪽·양쪽 리사이즈를 실행하고
   보이는 경계와 실제 재생 콘텐츠/automation을 확인합니다. 잘못된 형식·파일 경계는
   원본을 유지하며 실패해야 합니다. 템포 자동화가 있는 unwarped 변환은 지원 보류입니다.
10. 루프 시작 앞 도입부가 있는 클립, 부분 루프 길이, 길게 확장한 구간의 이음새를
    재생해 누락·중복·위상 오류가 없는지 확인합니다. 결과 clips[] 전체를 조회합니다.
11. 모든 Session 슬롯이 찬 상태의 오디오 트림 후 기존 클립과 Scene 개수를 확인합니다.
    보조 파일의 warp 설정이 지연되면 UNSUPPORTED인지 확인하고 재시도 전 목록을 봅니다.
12. Undo/Redo 및 실패 시 음소거 복구본의 위치·내용, 결과 조회 handle을 확인합니다.

Native MidiNoteSpecification/NoteVector 호출, 객체 동등성/무효화, Live callback/Undo,
오디오 가져오기와 clip automation 보존은 이 단계에서 최종 확인해야 합니다.
가장자리 trim 뒤 native 객체 identity, loop/marker setter의 실제 동작과 오디오 warp
변경 시점도 미확인입니다. 구현 완료와 native 실기 검증 완료를 구분합니다.

## 설치 및 Control Surface 이름 변경 — 2026-09-24

- 설치된 Live 12.4.6 Suite와 실제 User Library 경로를 확인했습니다. UI 설정 도중
  사용자가 직접 설정하기로 변경했으므로 자동 제어와 native 편집 테스트를 중단했습니다.
- 요청한 표시/설치 이름 `AbletonVVoori`를 installer와 연결 실패 안내에 적용했습니다.
  source package 이름은 유지하여 import와 upstream 원본 기록을 보존합니다.
- Live가 종료된 상태에서 설치 폴더를 `doc/local/backups/`에 백업한 뒤 새 이름으로
  변경했습니다. native 파일과 설정의 byte 일치, 무음 WAV 존재, 옛 폴더 부재를 확인했습니다.
- 이름 변경 검증: 기존 installer/helper 3개와 transport/client 7개 테스트 통과.
  wheel을 다시 제작하여 별도 venv에 설치, `AbletonVVoori` 대상 폴더와 native hash,
  설정, 무음 파일 및 실제 stdio 54개 도구 검색 통과. 전체 48개는 앞선 타임라인 검증 결과입니다.
- 이후 Live 실행/Control Surface 선택은 사용자가 수행합니다. native 동작 성공으로
  보고하지 않으며, 사용자 재개 요청 전까지 Live 화면을 조작하지 않습니다.
