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

제3자 구현을 그대로 복사하거나 종속시키지 않고 필요한 인터페이스를 확인한 뒤
독립적인 소규모 브리지를 작성했습니다. 외부 패키지는 MCP SDK와 그 의존성입니다.

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
