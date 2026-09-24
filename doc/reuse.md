# 다른 프로젝트에서 재사용

## 구성

```mermaid
flowchart LR
    A[MCP 클라이언트] -->|stdio JSON-RPC| B[Python MCP 서버]
    B -->|127.0.0.1 TCP / token| C[Remote Script 소켓]
    C -->|Live update_display| D[Arrangement API]
    D --> E[현재 Live Set]
```

| 경로 | 책임 |
| --- | --- |
| `src/ableton_arrangement_mcp/server.py` | 타입·입력 스키마·MCP 도구·stdio 실행 |
| `src/ableton_arrangement_mcp/client.py` | 로컬 TCP 요청·응답·제한 시간·오류 |
| `remote_script/AbletonArrangementMCP/api.py` | Arrangement 대상 확인, 검증, Live API 호출 |
| `remote_script/AbletonArrangementMCP/transport.py` | 인증·프레임 처리·중복 ID·nonblocking 소켓 |
| `remote_script/AbletonArrangementMCP/surface.py` | Live 진입, main-thread callback, 종료 |
| `scripts/configure.py` | 설정 생성, 명시한 User Library 설치, 업데이트 백업 |
| `scripts/export_conversation.py` | 지정한 세션의 공개 대화 메시지를 `doc/conversations/`에 복사 |
| `tests/` | 가짜 Live 모델, 실제 TCP·MCP 통합 검증 |

이 경로들은 프로젝트 루트 기준입니다. Python 클라이언트 패키지만 배포하면 Live
안에서 실행되는 Remote Script가 빠집니다. **다른 곳에 가져갈 때는 위 소스와
`pyproject.toml`, `scripts`, `doc`를 함께 복사**하고 새 환경에서 설치하세요.
`pip install .`은 MCP 서버만 설치합니다. Remote Script는 별도 단계입니다.

가상환경·캐시·인증 토큰·기존 대화 로그는 재사용 코드에 포함할 필요가 없습니다.
Live 안에 MCP/Pydantic 의존성을 넣지 마세요. 내부 브리지는 표준 라이브러리만
사용하며 Python 3.7 문법과 호환되도록 작성했습니다. 이는 Live 런타임 검증을
대신하지 않습니다. 외부 MCP 서버는 Python 3.10 이상입니다.

macOS도 Python/소켓 코드 구조는 동일합니다. `.venv/bin/python`으로 외부 서버를
실행하고, 실제 User Library를 `--user-library`로 지정하면 됩니다. macOS 설치와
Live 내부 동작은 이번 작업에서 검증하지 않았습니다.

## MCP 없이 호출하기

외부 Python 프로그램에서 다음처럼 기존 client를 직접 사용할 수 있습니다.
별도의 AI나 OpenAI API 연결은 필요하지 않습니다.

```python
from ableton_arrangement_mcp.client import BridgeClient

client = BridgeClient.from_file(r"Z:\Work\WorkAI\AbletonCtrl\doc\local\bridge.json")
status = client.call("status")
tracks = client.call("list_tracks", {"offset": 0, "limit": 100})
track_id = tracks["tracks"][0]["track_id"]
clips = client.call("list_clips", {"track_id": track_id})
```

## TCP 계약

이 TCP 서버는 MCP 서버 자체가 아니라 내부 브리지입니다. 연결당 한 요청과 한 응답을
UTF-8 JSON + LF로 교환하고 연결을 닫습니다. 호스트는 `127.0.0.1`로 고정합니다.

```json
{"id":"매 요청마다 새로운 UUID", "token":"로컬 설정의 토큰", "deadline":1790000000.0,
 "method":"list_tracks", "params":{"offset":0,"limit":100}}
```

`deadline` 예시 값은 실제 호출에 재사용하지 말고 `time.time() + 8`처럼 계산합니다.
최대 15초 이내의 Unix 시각이어야 합니다. 메서드 이름은 `api.py`의 `METHODS` 목록에
제한됩니다. 임의 Python 실행이나 객체 메서드 호출은 제공하지 않습니다.

```json
{"id":"요청과 동일", "result":{"tracks":[],"total":0,"offset":0}}
```

```json
{"id":"요청과 동일", "error":{"code":"STALE_HANDLE","message":"..."}}
```

프레임은 최대 1 MiB, 동시 소켓은 8개입니다. tick당 소켓별 수신·송신은 각각 최대
64 KiB입니다. 오래된 연결은 15초 뒤 닫습니다. 최근 2,048개 처리 ID만 기억하므로
영구적인 exactly-once 보장은 없습니다. 클라이언트는 원래부터 자동 재시도하지 않습니다.
시간이 만료된 요청은 Live API 호출 직전에 거부됩니다. 호출 후 응답 손실은 처리
완료 여부를 보장할 수 없으므로 새 조회로 상태를 확인해야 합니다.

읽기 작업도 반드시 Live main thread에서 실행합니다. 네트워크 스레드에서 Live
객체를 직접 접근하도록 변경하면 안 됩니다. 이 구조는 소켓 대기를 막지 않지만
단일 Live API 호출 자체가 오래 걸리는 것을 선점할 수는 없습니다.

## 기능 확장 순서

1. 공식 LOM과 해당 Live 버전에서 지원되는 Python 메서드·시그니처를 확인합니다.
2. `api.py`에 명시적 메서드를 추가하고 `METHODS` 허용 목록에 등록합니다.
3. 입력을 모두 확인한 뒤 `_mutate()` 안에서 필요한 Live 호출만 실행합니다.
4. MCP 도구의 스키마·설명·readOnly/destructive/idempotent annotation을 추가합니다.
5. 가짜 API 테스트와 실제 stdio 통합 테스트를 확장하고 별도 Live Set에서 검증합니다.

이동을 “복제 후 삭제”로 확장하면 부분 실패, 원본과 목적지 겹침, 자동화 보존을
다뤄야 합니다. 단순히 `clip.start_time`에 값을 쓰거나 loop marker를 Arrangement
시작 위치로 취급해서는 안 됩니다. 오디오 가져오기는 파일 존재·Live 지원 포맷·샘플
참조 경로와 변경되는 클립 길이를 확인하는 별도 기능으로 추가할 수 있습니다.

## 대화와 메모리 기록

작업 종료 시 `doc/PROJECT_MEMORY.md`, `doc/progress.md`, 해당 날짜 대화 기록을
갱신합니다. 전체 공개 메시지 복사는 다음 도우미를 사용합니다.

```powershell
.venv\Scripts\python scripts\export_conversation.py --session 'C:\경로\해당-session.jsonl'
```

정확히 지정한 파일의 `response_item` 중 user/assistant 텍스트만 복사합니다. 숨겨진
분석, system/developer 메시지, 도구 원본 출력은 내보내지 않습니다. 도구 조사 결과는
`research.md`와 `verification.md`에 남깁니다. 앱의 원본 로그는 이동·삭제하지 않습니다.
진행 중 로그의 마지막 미완성 줄은 건너뛰므로 종료 후 다시 실행하면 추가 메시지를
반영할 수 있습니다. 공개 메시지에 사용자가 직접 쓴 민감정보까지 자동 익명화하는
기능은 없으므로 대화 파일은 공유 전에 검토하세요.
