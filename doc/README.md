# Ableton Arrangement MCP

Ableton Live **12 Suite**의 Arrangement 클립을 MCP 클라이언트에서 다루기 위한
기본 구현입니다. 클립 이름이나 배열 번호 대신 현재 Live 연결에서 발급한 식별자로
대상을 지정합니다.

**현재 상태:** 기본 코드와 자동 검증을 제공하며, 실제 Live 내부 구동 검증은 남아
있습니다. 이 작업 환경에서는 실행 중인 Ableton을 발견하지 못했습니다. 연결 설정은
`doc/local/`에 생성했고, 실제 User Library 설치와 Control Surface 선택은 아직 하지 않았습니다.

## 제공 기능

| 대상 | 기능 |
| --- | --- |
| Live / 트랙 | 연결 상태, 버전, 템포, 박자, 트랙 목록, API 지원 여부 |
| Arrangement MIDI·오디오 클립 | 목록·상세, 이름·색상·음소거 변경, 같은 트랙 내 복제, 삭제 |
| Arrangement MIDI 클립 | 빈 클립 생성, 노트 조회·추가 |
| 편집 보호 | 오래된 식별자 거부, 겹치는 생성·복제 거부, 녹음·Freeze 중 편집 거부 |

직접 이동·트리밍, 다른 트랙으로 복사, Session 클립 편집, 오디오 파일 가져오기,
Take Lane/오토메이션 편집, Set 저장은 현재 도구에 포함하지 않았습니다.
음악 생성 AI나 외부 OpenAI API 키 없이 MCP 프로토콜로 동작합니다.

## 문서

- [설치와 연결](setup.md)
- [10개 MCP 도구와 사용 예](tools.md)
- [구조·프로토콜·다른 프로젝트 재사용](reuse.md)
- [인터넷 조사와 출처](research.md)
- [검증 결과와 Live 확인 절차](verification.md)
- [프로젝트 메모리](PROJECT_MEMORY.md)
- [설계](design.md), [구현 계획](implementation-plan.md), [작업 기록](progress.md)
- [현재 대화 기록](conversations/2026-09-24.md)

프로젝트 자료·대화 기록·메모리는 `doc/` 아래에 보관합니다. 다음 작업에서도 이를
따르도록 프로젝트 루트의 `AGENTS.md`에 규칙을 남겼습니다. Codex 앱 자체가 관리하는
세션 저장 위치는 이 규칙으로 바뀌지 않습니다.
