# AbletonCtrl 0.3

기존 [ahujasid/ableton-mcp](https://github.com/ahujasid/ableton-mcp)의 기능을 유지하고
Arrangement 클립 제어를 확장한 MCP입니다. **원본 37개 + 확장 17개 = 54개 도구**를
하나의 MCP 서버와 하나의 Live Remote Script에서 제공합니다.

**대상:** Ableton Live 12 Suite, Python 3.10 이상(외부 MCP 프로세스), Windows/macOS.
자동 테스트와 Windows 패키지 설치를 검증했습니다. **실제 Live 및 macOS 구동 검증은
아직 남아 있습니다.** 기능과 입력 규약 보존이 모든 Live 버전의 실행 성공을 뜻하지는 않습니다.

## 기능

| 영역 | 제공 기능 |
| --- | --- |
| 기존 MCP | Session·트랙 조회, MIDI/오디오 트랙 생성, 이름 변경, Session MIDI/오디오 클립 생성·실행·정지·삭제, 노트 조회·추가·삭제 |
| 장치·브라우저 | 파라미터 조회·변경, 브라우저 검색, 악기·이펙트·Drum Kit 로딩 |
| 기존 Arrangement | View 전환, 재생 위치·Locator, Session 클립을 Arrangement에 복사, 목록·이름 변경 |
| 확장 Arrangement | ID로 조회·선택, MIDI 생성, 오디오 가져오기, 동일/다른 트랙 복사·이동, 트리밍·리사이즈·삭제, 이름·색상·음소거 변경 |
| 확장 MIDI 편집 | 노트 조회·추가, note_id로 일부 노트 수정·삭제 |
| 선택적 데이터셋 | 원본 동의·의도·평가·선호·거절·청취 기록 도구 6개 유지. 기본 꺼짐, 음악 제어에 불필요 |

확장 생성·복제·이동은 기존 클립과 겹치면 거부합니다. 이동은 복사본을 검증한 뒤 원본을
삭제하며 새 clip_id를 반환합니다. 오디오 가져오기는 길이를 미리 알 수 없어 트랙의
마지막 클립 이후에서만 허용합니다. 원본 도구는 기존 입력·동작을 유지하므로 이 보호
규칙이 원본 도구 전체에 적용되지는 않습니다.

트리밍·리사이즈는 절대 song beat로 양 끝을 지정합니다. 루프 클립 확장은 최대 64개의
연속 클립으로 결과를 반환할 수 있습니다. 원본을 검증된 복사본으로 교체하므로 반환된
모든 새 ID를 사용하세요. 오디오 트리밍에는 새 설치 도우미가 만드는 `silence.wav`가
필요합니다. [타임라인 편집·복구 설명](timeline-editing.md)을 참고하세요.

**제공하지 않는 작업:** 다른 클립을 덮어쓰는 편집, 원본과 겹치는 구간으로 이동,
Take Lane/Comping/오토메이션 직접 편집, 자동 Set 저장.

## 가져다 사용하기

```powershell
git clone https://github.com/wooguylee/AbletonCtrl.git
cd AbletonCtrl
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install .
.venv\Scripts\python scripts\configure.py --user-library 'D:\Ableton\User Library'
```

마지막 경로는 Live 설정에서 확인한 실제 User Library로 바꿉니다. Live를 재시작하고
Control Surface에 `AbletonVVoori`를 선택합니다. 기존 `AbletonMCP` 선택과
이전 MCP 클라이언트 등록은 해제하고, 생성된 `doc/local/codex-config.toml` 또는
`doc/local/mcp-client.json`을 클라이언트 설정에 병합합니다.

자세한 순서와 연결 검사는 [설치·전환 안내](setup.md), 다른 PC와 macOS는
[English quickstart](quickstart-en.md)를 참고하세요. 특정 Ableton MCP 제품을 써야 하는
제약은 없습니다. Codex는 이 프로젝트 같은 stdio MCP 서버를 등록해 사용할 수 있습니다.

## 문서

- [설치·Codex 연결·기존 MCP에서 전환](setup.md)
- [English quickstart](quickstart-en.md)
- [54개 도구와 호출 예](tools.md)
- [타임라인 트리밍·리사이즈·트랙 간 복사와 복구](timeline-editing.md)
- [원본 호환성·라이선스·선택적 데이터셋](compatibility.md)
- [코드 구조·프로토콜·재사용](reuse.md)
- [인터넷 조사와 근거](research.md)
- [검증 결과·실제 Live 점검](verification.md)
- [프로젝트 메모리](PROJECT_MEMORY.md), [대화 기록](conversations/2026-09-24.md)

원본 기준은 commit `9dddc7bd5b95412510fdeb745949e3bf23f3fd8a` (MCP 1.4.5,
Remote Script 1.7.1)입니다. 자동으로 upstream 최신 버전을 내려받지 않습니다.
토큰·가상환경·개인 대화 원본은 Git에 포함하지 않습니다.
