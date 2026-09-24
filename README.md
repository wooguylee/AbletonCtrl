# AbletonCtrl

[ahujasid/ableton-mcp](https://github.com/ahujasid/ableton-mcp)의 원본 도구 37개와
Arrangement 확장 도구 17개, **총 54개 MCP 도구**를 제공합니다.
Session·장치 제어와 Arrangement 클립 생성·복사·이동·트림·리사이즈·MIDI 노트 편집을
하나의 MCP 서버와 Live Remote Script로 사용할 수 있습니다.

대상은 **Ableton Live 12 Suite**입니다. Windows Live 12.4.6 Suite에서 실기 검증했으며,
macOS는 미검증입니다. 현재 버전 0.3.1의 범위와 제한은 아래에 안내합니다.

## 다른 PC의 Codex에 전달하기

**Ableton이 설치된 PC의 로컬 Codex 작업**에 아래 문장만 전달하면 됩니다.

```text
https://github.com/wooguylee/AbletonCtrl.git
README.md를 참조해서 이 PC에 설치하고 Codex MCP로 사용할 수 있도록 설정해줘.
```

이 README에 설치·등록·전환·연결 확인 절차가 포함되어 있습니다.
GitHub URL로 소스를 가져온 뒤 로컬 stdio 서버를 등록합니다.
**MCP 프로세스와 Ableton Live는 같은 PC에서 실행해야 합니다.**

## 설치를 수행하는 Codex의 작업 순서

1. 저장소를 안정적인 로컬 폴더에 clone하고 `AGENTS.md`를 읽습니다. 기존 checkout이
   있다면 변경 사항을 확인하고 보존합니다. 이 PC의 OS·Git·Python을 확인합니다.
2. 아래 명령으로 별도 `.venv`에 패키지를 설치합니다. 외부 Python은 3.10 이상이며
   검증 환경은 3.12입니다. 다른 PC의 `.venv`나 `doc/local`을 복사하지 않습니다.
3. Live의 **Settings/Preferences → Library → Location of User Library**에서 실제
   User Library 경로를 확인합니다. 확인할 수 없으면 사용자에게 경로를 물어봅니다.
4. `scripts/configure.py --user-library <실제 경로>`로 **AbletonVVoori** Remote Script와
   이 PC용 연결 설정을 설치합니다. 인증 토큰은 새로 생성되며 출력하거나 공유하지 않습니다.
5. 생성된 `doc/local/codex-config.toml`의 `[mcp_servers.abletonctrl]` 항목을
   **사용자 Codex 설정**에 병합하여 다른 프로젝트에서도 사용할 수 있게 합니다.
   기존 설정을 백업하고 다른 MCP 항목은 유지합니다. 설치 도우미는 설정 예를 생성하며,
   이 병합 작업은 별도로 수행해야 합니다.
6. 기존 `ahujasid/ableton-mcp` 등록이 있다면 해당 MCP 항목만 비활성화합니다.
   기존 Live Control Surface **AbletonMCP**도 해제하도록 사용자에게 안내합니다.
   원본 9877 서버와 새 인증 bridge(기본 8765)는 함께 섞어 사용할 수 없습니다.
7. 아래의 사용자 설정 순서를 안내하고, 완료되면 **읽기 작업으로 연결을 검증**합니다.
   현재 곡을 수정하거나 재생하지 않습니다. 쓰기 테스트는 사용자가 요청할 때 별도 Set에서
   실행합니다. 작업 기록·메모리·로컬 설정은 이 프로젝트의 `doc/` 아래에 남깁니다.

### Windows 설치 명령

```powershell
git clone https://github.com/wooguylee/AbletonCtrl.git
cd AbletonCtrl
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install .
.venv\Scripts\python scripts\configure.py --user-library 'D:\Ableton\User Library'
```

마지막 경로는 예시이므로 반드시 이 PC의 실제 User Library로 바꿉니다.
이미 AbletonVVoori가 설치되어 있으면 Live를 닫고 같은 명령에 `--replace`를 추가합니다.
기존 설치본은 `doc/local/backups/`에 백업됩니다.

macOS에서는 `python3 -m venv .venv`와 `.venv/bin/python`을 사용합니다.
자세한 명령은 [English quickstart](doc/quickstart-en.md)에 있습니다.
Live의 내부 Python API를 별도 `pip install Live`로 설치하지 않습니다.

### Codex MCP 등록

여러 프로젝트에서 쓰려면 생성된 MCP 항목을 `~/.codex/config.toml`에 병합합니다.
`CODEX_HOME`을 별도로 지정했다면 그 위치의 설정 파일을 사용합니다.
특정 프로젝트에서만 쓰려면 해당 프로젝트의 `.codex/config.toml`에 병합하고
신뢰된 프로젝트에서 실행합니다. 두 범위에 중복 등록할 필요는 없습니다.

설정의 `command`와 `args`는 설치 도우미가 생성한 **이 PC의 절대 경로**를 사용합니다.
다른 컴퓨터의 설정이나 인증 토큰을 그대로 복사하지 않습니다. MCP 서버는 Codex가
등록된 명령으로 실행합니다. 설치 폴더를 옮기면 설정을 다시 생성·병합해야 합니다.
설정 방식은 [공식 Codex MCP 문서](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)를 참고하세요.

## 사용자가 Live에서 설정할 순서

1. 설치 완료 후 **Live를 재시작**합니다.
2. **Settings/Preferences → Link, Tempo & MIDI → Control Surface**에서
   **AbletonVVoori**를 한 슬롯에 선택합니다. MIDI Input/Output은 **None**으로 둘 수 있습니다.
3. 이전 **AbletonMCP** 또는 **AbletonArrangementMCP** 선택이 남아 있다면 **None**으로
   바꿔 중복 실행을 방지합니다.
4. Codex의 MCP 서버를 재시작하거나 새 작업을 열고 연결 확인을 요청합니다.

## 연결 확인과 완료 기준

Windows에서 프로젝트 루트를 기준으로 다음을 실행합니다. Set을 변경하지 않습니다.

```powershell
.venv\Scripts\python -m ableton_arrangement_mcp --config '.\doc\local\bridge.json' --check
```

이어서 **Codex에 등록된 MCP를 통해** 다음을 확인합니다.

- 도구 목록에 현재 버전 기준 **54개 도구**가 있는지 확인합니다.
- `ableton_status`로 Live 버전과 bridge 버전 **0.3.1**을 확인합니다.
- `get_remote_script_info`로 **AbletonCtrl** 스크립트 연결을 확인합니다.
- `ableton_list_tracks`로 받은 `track_id`를 사용하여
  `ableton_list_arrangement_clips`를 호출합니다. 빈 Set은 빈 클립 목록이 정상입니다.

도구 목록 검색만 성공한 상태와 실제 Live 연결 성공을 구분하여 보고합니다.
연결 실패 시 Live 실행·Control Surface 선택·포트·설치본 설정을 확인합니다.
문제 해결과 업데이트 방법은 [설치 안내](doc/setup.md)를 참고하세요.

## 기능 제한과 검증

- Warp Off 오디오의 지연 리사이즈는 Undo/Redo가 여러 단계로 나뉠 수 있습니다.
  기존 clip envelope가 있는 지연 리사이즈는 거부합니다.
- Locator는 **첫 항목 생성과 기존 이름 변경**만 허용합니다. 추가 생성은 Live에서
  직접 해야 합니다. 그리드 스냅으로 기존 Locator가 삭제되는 native 동작을 방지합니다.
- 다른 클립 덮어쓰기, comping, 오토메이션 직접 편집과 자동 Set 저장은 제공하지 않습니다.
- 데이터셋 수집은 기본 꺼짐이며 음악 제어에 외부 backend나 OpenAI API 키가 필요하지 않습니다.

실제 MCP 도구 54개·93회 호출과 자동 테스트 61개를 검증했습니다.
정확한 시나리오·미검증 범위·재실행 방법은 [실기 보고서](doc/live-verification-2026-09-25.md),
각 도구의 호출 예는 [도구 설명](doc/tools.md), 편집·복구는
[타임라인 안내](doc/timeline-editing.md)에 있습니다.

상세 문서·조사·대화·프로젝트 메모리는 [doc/](doc/README.md)에 보관합니다.
원본 코드의 MIT 라이선스와 출처를 포함합니다.
