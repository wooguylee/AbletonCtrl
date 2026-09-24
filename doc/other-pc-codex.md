# 다른 PC의 Codex에서 사용하기

Ableton Live가 설치된 PC의 **로컬 Codex 작업**에서 아래 요청문을 전달합니다.
GitHub 주소는 소스를 가져오는 주소입니다. 설치 후 실행하는 로컬 stdio 프로세스를
MCP 서버로 등록합니다. 이 프로젝트의 MCP 프로세스와 Live는 같은 PC에서 실행합니다.

## Codex에 전달할 요청문

```text
https://github.com/wooguylee/AbletonCtrl.git 을 이 PC에 설치해서
Codex에서 Ableton Live 12 Suite를 MCP로 제어할 수 있게 설정해줘.

1. 안정적인 로컬 설치 폴더에 저장소를 clone하고 AGENTS.md,
   doc/setup.md, doc/other-pc-codex.md, doc/live-verification-2026-09-25.md를 읽어줘.
2. 이 PC의 OS와 Python을 확인하고 별도 .venv에 패키지를 설치해줘.
3. Live의 실제 User Library 경로를 확인해서 scripts/configure.py로
   AbletonVVoori Remote Script와 이 PC용 연결 설정을 설치해줘.
   경로를 확인할 수 없으면 나에게 경로를 물어봐줘.
4. 생성된 doc/local/codex-config.toml의 abletonctrl 항목을
   내 사용자 Codex 설정에 병합해서 다른 프로젝트에서도 쓸 수 있게 해줘.
   기존 설정을 백업하고 다른 MCP 항목은 유지해줘.
5. 기존 ahujasid/ableton-mcp 등록이 있으면 기존 항목만 비활성화해줘.
   Live에서도 기존 AbletonMCP 대신 AbletonVVoori를 선택하도록 안내해줘.
6. Live Control Surface 설정과 필요한 Codex 재시작은 내가 할 수 있게 알려줘.
   설정 완료 후 --check, MCP 도구 목록, ableton_status,
   get_remote_script_info, Arrangement 목록 조회까지 실제 연결을 확인해줘.
7. 연결 확인에서는 현재 곡을 수정하거나 재생하지 말고,
   쓰기 테스트는 별도 테스트 Set에서 내가 요청할 때 진행해줘.
8. 작업 기록과 로컬 설정은 이 설치 프로젝트의 doc 아래에 남겨줘.
   다른 PC의 .venv, doc/local, 인증 토큰은 복사해서 사용하지 말아줘.
```

저장소가 비공개라면 해당 PC에서 저장소를 읽을 수 있는 GitHub 인증이 필요합니다.
기존 폴더가 있으면 새로 덮어쓰지 않고 상태를 확인한 뒤 업데이트합니다.

## 사용자가 확인할 순서

1. Live의 Settings/Preferences → Library에서 실제 User Library 경로를 확인합니다.
2. Codex의 설치 완료 안내 후 Live를 재시작합니다.
3. Settings/Preferences → Link, Tempo & MIDI → Control Surface에서
   **AbletonVVoori**를 한 슬롯에 선택합니다. MIDI Input/Output은 None으로 둘 수 있습니다.
4. 이전 **AbletonMCP** Control Surface는 None으로 바꿉니다.
5. Codex의 MCP 서버를 재시작하거나 새 작업을 열고 연결 확인을 요청합니다.

이 저장소를 설치한 현재 기준(0.3.1)은 **54개 도구**입니다. 도구 목록 검색 성공과
실제 Live 연결 성공은 별도이므로 `ableton_status` 응답까지 확인합니다.
설치 폴더를 옮기면 설정의 절대 경로가 달라지므로 설치 도우미 실행과 MCP 설정 병합을
다시 해야 합니다. MCP 서버는 등록된 실행 명령으로 Codex가 시작합니다.

## Codex 설정 범위

여러 프로젝트에서 쓰려면 생성된 `[mcp_servers.abletonctrl]` 테이블을 사용자 설정
`~/.codex/config.toml`에 병합합니다. `CODEX_HOME`을 별도로 지정했다면 그 위치의
설정 파일을 사용합니다. 특정 프로젝트에서만 쓰려면 그 프로젝트의
`.codex/config.toml`에 병합하고 신뢰된 프로젝트에서 실행합니다.
이 설치 도우미는 설정 예만 생성하며 사용자 설정을 자동 변경하지 않습니다.
Codex의 stdio 및 사용자/프로젝트 설정 방식은
[공식 MCP 문서](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)를 참고하세요.

실제 설치 명령은 [설치 안내](setup.md), macOS는 [English quickstart](quickstart-en.md),
기능 제한과 재현 가능한 테스트는 [실기 보고서](live-verification-2026-09-25.md)에 있습니다.
