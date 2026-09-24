# Arrangement 제어 조사 — 2026-09-24

## 확인한 근거

| 출처 | 확인한 내용과 적용 |
| --- | --- |
| [Cycling '74 Track LOM](https://docs.cycling74.com/apiref/lom/track/) | `arrangement_clips`는 Live 11부터 제공. MIDI 생성, Arrangement 복제, 클립 삭제 API를 기본 기능으로 선택 |
| [Cycling '74 Clip LOM](https://docs.cycling74.com/apiref/lom/clip/) | Arrangement `start_time`·`end_time`은 읽기 속성. 이름·색상·muted는 수정 가능. loop·marker는 별도 내부 좌표 |
| [Ableton Remote Script 설치](https://help.ableton.com/hc/en-us/articles/209072009-Installing-third-party-remote-scripts) | User Library의 `Remote Scripts`에 설치하고 Live의 Control Surface에서 선택하는 경로 |
| [AbletonOSC 프로젝트](https://github.com/ideoforms/AbletonOSC) | Python Remote Script를 통해 외부 프로세스와 연결하는 기존 접근 방식 비교 |
| [AbletonOSC clip.py](https://github.com/ideoforms/AbletonOSC/blob/master/abletonosc/clip.py) | 기존 clip handler는 Session `clip_slots`를 선택. Python에서 `get_notes_extended`는 note 객체를 반환하며 `Live.Clip.MidiNoteSpecification` 튜플을 `add_new_notes`에 전달 |
| [공식 MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) | stdio 서버·클라이언트와 도구 스키마를 구현하는 SDK. v1 범위 사용 |
| [공식 Codex MCP 설정](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) | 프로젝트 또는 사용자 config.toml의 `mcp_servers`에 command·args 등록 |

초기 버전은 독립 Arrangement bridge였으나 사용자의 원본 호환 요구에 따라
현재 버전은 ahujasid/ableton-mcp의 MCP 도구·Live handler를 MIT 조건으로 포함합니다.
기존 코드의 SHA256과 고정 commit은 `upstream-source.json`에 기록했습니다.
외부 기본 의존성은 MCP SDK이며 선택적 dataset extra만 Supabase SDK를 사용합니다.

## 중요한 구분

Cycling '74의 LOM은 Max for Live용 공개 문서입니다. Python Remote Script는 같은
Live 객체 모델에 접근하지만 파라미터와 반환값 표현이 다를 수 있습니다. 특히
노트 추가는 Max의 JSON dictionary 형식을 그대로 Python에 넘기지 않습니다.
기능 존재는 실행 시 검사하고, 실제 메서드 동작 검증은 설치한 Live 안에서 수행해야 합니다.

Live 12 Suite에서 Max for Live 방식도 사용할 수 있지만, 이 기본 구현에서는
Set마다 장치를 넣을 필요가 없는 Remote Script를 선택했습니다. 향후 내부 adapter를
Max for Live로 교체해도 MCP 도구 이름과 브리지 요청 계약을 유지할 수 있습니다.

Arrangement 시작·끝 시간을 직접 변경하는 구현, 키보드·마우스 조작, `.als` 압축
XML 수정은 사용하지 않았습니다. 전자는 공개 지원 범위가 다르고, 후자는 현재 Set의
상태·화면·파일 저장 상태에 의존하므로 이번 기초 코드의 범위에서 제외했습니다.

## 재현 시 주의

조사 시점의 문서를 기준으로 했으며 Live 세부 버전에 따라 지원이 달라질 수 있습니다.
현재 버전과 API capability는 `ableton_status`, `ableton_list_tracks`로 확인합니다.
조회되는 capability는 메서드 존재 여부이며 해당 작업의 성공을 미리 보증하지 않습니다.
SDK 설치 버전은 `requirements-tested.txt`, 실행 결과는 `verification.md`에 기록합니다.

## 원본 MCP 통합 조사

[원본 고정 버전](https://github.com/ahujasid/ableton-mcp/tree/9dddc7bd5b95412510fdeb745949e3bf23f3fd8a)을
확인하고 37개 공개 도구의 이름·함수 시그니처를 `upstream-tools.json`에 저장했습니다.
조사 시점 main에는 Arrangement 조회·이름·Session 복사 등의 일부 기능이 이미 있습니다.
사용자의 다른 PC에 설치된 과거 버전은 직접 확인하지 않았습니다.

원본은 MCP 프로세스와 Live Remote Script를 TCP로 연결합니다. 여기서는 음악 처리
본문을 보존하면서 한 개의 인증 bridge로 라우팅하고 원본의 별도 네트워크 스레드를
생성하지 않습니다. 원본 dataset/telemetry 기능은 명시적인 설정과 동의가 있는 경우에만
사용하도록 기본 비활성화했습니다. 호환 범위는 [compatibility.md](compatibility.md)에 있습니다.

공식 Clip LOM에서 `get_notes_by_id`, `apply_note_modifications`, `remove_notes_by_id`를
확인해 MIDI 노트를 지우고 다시 만드는 대신 ID 기준 편집을 추가했습니다. Max LOM의
dictionary 표기를 Python 객체 호출로 바꾸는 부분은 실제 Live 12에서 확인해야 합니다.
