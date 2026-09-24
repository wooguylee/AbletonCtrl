# 검증 결과 — 2026-09-24

## 결과

**자동 테스트 20/20 통과.** 기본 MCP 코드·설치 도우미·문서 구현을 완료했습니다.
실제 Ableton Live 프로세스 안에서의 실행은 아직 검증하지 않았습니다.

| 검사 | 결과 |
| --- | --- |
| Python 환경 | Python 3.12.10, MCP SDK 1.30.0, Windows |
| `pip install -e .` | 성공 |
| `python -m pip check` | No broken requirements found |
| `python -m unittest discover -s tests -v` | 20 tests, OK |
| `python -m compileall -q src remote_script scripts tests` | 성공 |
| Remote Script 4개 파일 Python 3.7 문법 파싱 | 성공; 실제 내장 런타임 검증을 뜻하지 않음 |
| stdio MCP subprocess | initialize → 10개 도구 검색 → 상태/생성/편집/노트/복제/삭제/오류 처리 통과 |
| Live 연결 `--check` | `BRIDGE_UNAVAILABLE`, exit 1. Live 미실행·미설치 상태 |
| 검증 후 프로세스/포트 | 테스트가 띄운 MCP 프로세스 종료, 기본 8765 listening 없음 |

전체 자동 테스트 출력: [test-results.txt](test-results.txt).
설치된 패키지 버전: [requirements-tested.txt](requirements-tested.txt).
버전 목록은 이번 Windows 환경의 기록이며 다른 운영체제에서는 `pyproject.toml`로
의존성을 설치하세요.

## 확인한 동작

- 클립 순서 변경 후에도 원래 대상 편집, 삭제·트랙 제거 후 오래된 식별자 거부.
- 생성·복제·삭제, Undo 단계 균형, native API 예외 후 Undo 단계 종료.
- 겹치는 구간, 잘못된 타입·숫자·필드, Freeze·녹음 모드, 지원되지 않는 API 거부.
- clip-local MIDI 노트 좌표, pitch 127 포함 조회, 스펙 객체로 노트 추가.
- 실제 TCP의 분할 프레임, 인증 실패, 만료, malformed JSON, 1 MiB 초과 연결 종료.
- 같은 쓰기 요청 ID 재사용 시 추가 실행 방지, 타임아웃 뒤 늦게 도착한 생성 미실행.
- 실제 MCP 도구 schema/annotation/structuredContent와 오류의 `isError` 전파.
- 설치 실패 시 기존 설정 보존, 설치 업데이트 백업, 공개 대화와 숨겨진 메시지 분리.

## 독립 코드 검토

별도 읽기 전용 검토에서 두 문제를 재현했고 회귀 테스트로 수정했습니다.

1. 설치 실패 전에 로컬 포트를 바꾸던 문제: 대상 확인·복사 이후에 연결 설정 저장.
2. 환경 정보로 시작한 사용자 메시지의 실제 요청이 빠지던 문제: 알려진 앞부분
   메타데이터 블록만 제거하고 나머지 사용자 텍스트 보존.

두 테스트 모두 수정 전 실패와 수정 후 성공을 확인했습니다. 검토자가 확인하지
못한 native 동작은 아래 Live 검증으로 남겼습니다. 기본 API/전송 코드에서 추가로
확인된 차단 문제는 없었지만 실제 Live 호환성을 보증하는 검토 결과는 아닙니다.

## Live 12 Suite에서 남은 수동 검증

실제 사용자 Set 대신 **새 빈 Set 또는 별도 사본**에서 확인합니다.

1. [설치 안내](setup.md)에 따라 정확한 User Library에 설치하고 Control Surface 활성화.
2. `--check`에서 실제 Live 버전 출력. `ableton_list_tracks`에서 필요한 capability 확인.
3. 빈 MIDI 트랙에 beat 0, 길이 4인 클립을 생성하고 4개 음표를 넣어 화면·재생 확인.
4. 이름·색상·muted 변경 후 상세 조회와 화면이 일치하는지 확인.
5. beat 4로 복제한 뒤 위치·길이·노트 유지 확인. 복제본만 삭제하고 Live Undo 확인.
6. 별도 오디오 클립, 루프 반복 클립, 잘린 클립으로 같은 트랙 복제를 확인.
   타임라인 외곽 길이와 실제 복제 범위가 같은지 확인해야 합니다.
7. UI에서 클립/트랙 순서 변경·삭제·Undo 후 오래된 식별자가 다른 대상을 가리키지 않는지 확인.
8. 모달 창·Set 변경·Live 재시작 후 재연결, Control Surface 해제 시 소켓 종료 확인.

Max LOM과 Python Remote Script의 메서드 반환값, Live 객체 무효화·동등성, 실제 MIDI
생성자, `update_display` callback과 Undo 동작은 이 단계에서 최종 확인해야 합니다.
현재 구현은 이를 위한 기본 코드와 재현 가능한 검증 경로를 제공합니다.
