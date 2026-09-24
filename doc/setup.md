# 설치와 연결

## 1. 외부 Python 환경

외부 MCP 서버는 Python 3.10 이상, Live 내부 스크립트는 Live가 제공하는 Python을
사용합니다. **외부 Python에 `Live` 패키지를 pip 설치하지 않습니다.**
검증 환경은 Windows / Python 3.12.10 / MCP SDK 1.30.0입니다.

PowerShell에서 프로젝트 루트로 이동한 다음 실행합니다.

```powershell
git clone https://github.com/wooguylee/AbletonCtrl.git
cd AbletonCtrl
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install .
.venv\Scripts\python scripts\configure.py
```

설정 도우미는 다음을 생성합니다.

- `doc/local/bridge.json`: 임의의 인증 토큰, TCP 포트(기본 8765), 제한 시간.
- `doc/local/codex-config.toml`: 이 컴퓨터의 절대 경로가 반영된 Codex 설정 예.
- `doc/local/mcp-client.json`: stdio MCP를 지원하는 다른 클라이언트용 설정 예.

토큰 값은 화면에 출력하지 않습니다. `doc/local/`은 Git에서 제외됩니다. 같은
설치에 도우미를 다시 실행하면 기존 토큰을 재사용합니다. 다른 컴퓨터에 옮길 때는
이 폴더와 `.venv`를 복사하지 말고 새 환경에서 다시 생성하세요.

## 2. Live Remote Script 설치

Live의 **Settings/Preferences → Library → Location of User Library**에서 실제
User Library 경로를 확인합니다. 다음 경로는 예시이며 자신의 경로로 바꿔야 합니다.

```powershell
.venv\Scripts\python scripts\configure.py --user-library 'D:\Ableton\User Library'
```

도우미가 `User Library/Remote Scripts/AbletonArrangementMCP/`에 Python 파일과
`config.json`을 복사합니다. 사용자 라이브러리 경로를 추측해 자동 설치하지 않습니다.
이미 설치된 것을 업데이트하려면 Live를 닫고 다음처럼 실행합니다.

```powershell
.venv\Scripts\python scripts\configure.py --user-library 'D:\Ableton\User Library' --replace
```

기존 폴더 사본은 프로젝트 `doc/local/backups/`에 저장됩니다. 관리하는 파일을
덮어쓰며, 설치 폴더의 별도 사용자 파일은 삭제하지 않습니다.

Live를 재시작하고 **Settings/Preferences → Link, Tempo & MIDI → Control Surface**에서
`AbletonArrangementMCP`를 한 슬롯에 선택합니다. 하드웨어 MIDI Input/Output은 `None`으로
둘 수 있습니다. 정상 시작하면 상태 표시줄에 `Arrangement MCP ready`가 나타납니다.
포트를 바꾸려면 `--port 8766`처럼 지정하고 양쪽 설정을 갱신한 뒤 Live를 재시작합니다.

공식 설치 위치와 선택 절차: [Ableton Remote Script 설치 안내](https://help.ableton.com/hc/en-us/articles/209072009-Installing-third-party-remote-scripts).

## 3. 연결만 먼저 확인

```powershell
.venv\Scripts\python -m ableton_arrangement_mcp --config 'Z:\Work\WorkAI\AbletonCtrl\doc\local\bridge.json' --check
```

이 명령은 Set을 바꾸지 않고 실제 Live 버전과 상태를 JSON으로 출력합니다.
`BRIDGE_UNAVAILABLE`은 Live 미실행, 스크립트 미선택, 설치 오류 또는 포트 불일치를
뜻할 수 있습니다. Live가 없는 상태에서 서버 도구 목록을 열 수 있는 것과 실제
Live 연결 성공은 별개입니다.

## 4. Codex 연결

`doc/local/codex-config.toml`의 내용을 프로젝트 `.codex/config.toml`의 기존 설정과
병합합니다. 설정 파일이 없다면 다음처럼 복사할 수 있습니다.

```powershell
New-Item -ItemType Directory -Force .codex
Copy-Item -LiteralPath 'doc\local\codex-config.toml' -Destination '.codex\config.toml'
```

위 복사 명령은 `.codex/config.toml`이 **없을 때만** 사용하세요. 다른 설정이 있으면
덮어쓰지 말고 해당 MCP 테이블만 추가합니다. 새 Codex 작업/세션에서 MCP 목록을 확인한
뒤 `ableton_status`를 호출합니다. 프로젝트 설정은 Codex의 프로젝트 신뢰 정책에 따라
적용됩니다. 이 구현은 전역 Codex 설정을 자동 변경하지 않습니다.
설정 키는 [공식 MCP 설정 문서](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)를 참고했습니다.

다른 MCP 클라이언트에는 `doc/local/mcp-client.json`의 서버 항목을 그 클라이언트가
요구하는 설정 위치에 병합합니다. `command`는 이 프로젝트의 가상환경 Python,
`args`는 `-m ableton_arrangement_mcp --config <절대 경로>`입니다.

## 문제 해결 / 해제

| 증상 | 확인할 것 |
| --- | --- |
| Control Surface 목록에 없음 | 폴더가 정확히 `Remote Scripts/AbletonArrangementMCP`인지, Live를 재시작했는지 |
| startup failed | Live의 `%APPDATA%/Ableton/Live <version>/Preferences/Log.txt`에서 `Arrangement MCP` 검색 |
| UNAUTHORIZED | 프로젝트 `bridge.json`과 설치 폴더 `config.json`의 토큰을 설치 도우미로 동기화 |
| 포트 사용 중 | 중복 Control Surface 선택을 해제하거나 양쪽 포트 변경 |
| UNSUPPORTED | `ableton_list_tracks`의 capability와 실제 Live 세부 버전 확인 |
| STALE_HANDLE | 트랙/클립 목록을 다시 조회한 뒤 새 식별자 사용 |
| timeout / outcome unknown | Live 모달 창을 닫고 상태를 조회. 쓰기 명령을 곧바로 재전송하지 않기 |
| OVERLAP | 빈 타임라인 구간을 선택. 덮어쓰기 기능은 제공하지 않음 |

해제는 Live의 해당 Control Surface를 `None`으로 바꾸고 MCP 클라이언트 설정 항목을
제거하면 됩니다. 소켓은 Remote Script의 `disconnect()`에서 닫습니다.

## Codex에서 반드시 특정 Ableton MCP를 사용해야 하나요?

아닙니다. Codex는 MCP 서버를 등록해 제공되는 도구를 호출하므로, 특정 Ableton MCP
제품으로 고정되지 않습니다. Codex가 지원하는 로컬 stdio 또는 Streamable HTTP
방식으로 호환되게 구현한 서버라면 직접 만든 서버도 연결할 수 있습니다.
근거: [공식 MCP 지원 기능과 등록 방법](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).

이 프로젝트에서는 원본 ableton-mcp 기능에 Arrangement 확장을 더한 `AbletonCtrl`을 사용합니다.
연결 구조는 `Codex → stdio MCP 서버 → 로컬 TCP → 통합 Live Remote Script → Session·장치·Arrangement`입니다.
Codex에는 MCP 서버를 등록하고, Live에는 함께 제공하는 Remote Script를 설치·활성화합니다.
이 구현은 loopback에 연결하므로 MCP 프로세스와 Live를 같은 컴퓨터에서 실행합니다.

어떤 MCP를 선택할지는 실제 지원 기능에 따라 결정합니다. MCP 연결 성공만으로
Arrangement 제어가 보장되지는 않으며, 선택한 서버가 필요한 클립 조회·생성·편집
도구와 Live 측 동작을 구현해야 합니다. 현재 구현의 범위와 검증 한계는
[도구 설명](tools.md)과 [검증 기록](verification.md)에 구분해 두었습니다.

## 기존 ahujasid/ableton-mcp에서 전환

1. 기존 Live `AbletonMCP` Control Surface를 `None`으로 바꿉니다.
2. 이 저장소를 설치하고 함께 제공하는 `AbletonArrangementMCP`를 활성화합니다.
3. 클라이언트의 기존 `ableton-mcp`/`uvx ableton-mcp` 서버 등록을 해제합니다.
4. 생성된 `abletonctrl` MCP 항목을 등록합니다. 기존 0.1 버전의
   `ableton_arrangement` 항목이 있으면 이 항목으로 교체합니다.
5. 새 MCP 세션에서 54개 도구, `ableton_status` 버전 0.3.0,
   `get_remote_script_info`의 name AbletonCtrl과 원본 commit을 확인합니다.

원본 도구의 이름·입력 형식은 유지하지만 네트워크 프로토콜은 바뀌었습니다.
원본의 9877 TCP 서버와 이 프로젝트의 인증 bridge(기본 8765)를 섞지 않습니다.
기존 설정·Remote Script를 삭제할 필요는 없으며 비활성화한 상태로 보관할 수 있습니다.
원본 클립/트랙 index는 그대로 쓰고, 새 `ableton_` 도구는 목록에서 받은 ID를 씁니다.
긴 오디오 가져오기·브라우저 작업을 위해 생성된 Codex tool_timeout_sec는 180초입니다.

소스 복제 없이 Git/pip로 설치하거나 macOS에서 사용하는 방법은
[English quickstart](quickstart-en.md)를 참고하세요. wheel에도 Live Script가 포함됩니다.
설정 파일과 Live 스크립트의 실제 활성화는 여전히 별도 단계입니다.

## 0.3 타임라인 편집으로 업데이트

Live를 종료하고 `git pull`, `.venv\Scripts\python -m pip install .` 후 설치 도우미를
같은 `--user-library` 경로와 `--replace`로 실행합니다. 기존 폴더는
`doc/local/backups/`에 백업되고 토큰은 유지됩니다. 이번 버전은 오디오 트리밍에
사용할 1초 PCM 무음 파일 `silence.wav`도 설치 폴더에 생성합니다. MCP 서버만
업데이트하면 새 native 명령/파일을 사용할 수 없으므로 Remote Script도 교체하세요.
Live와 MCP 클라이언트를 다시 시작한 뒤 버전 0.3.0을 확인합니다.
