# 원본 호환성 및 라이선스

## 고정 기준

- 원본: [ahujasid/ableton-mcp](https://github.com/ahujasid/ableton-mcp)
- commit: `9dddc7bd5b95412510fdeb745949e3bf23f3fd8a`
- 원본 MCP package 1.4.5 / Remote Script 1.7.1
- [37개 이름·시그니처 원본 기록](upstream-tools.json)
- [복사한 16개 Python 파일 경로·SHA256](upstream-source.json)
- MIT License, Copyright (c) 2025 Siddharth Ahuja. 루트 및 배포 패키지에 LICENSE 포함.

모든 원본 도구의 이름, 인수 이름·기본값·입력 JSON Schema를 유지합니다. 함수와 Live
handler 원문을 포함하며, 외부 서버의 전송 연결과 Live 측 실행 스케줄링만 adapter로
교체합니다. schema 비교 테스트와 원본 source hash 검사가 변경 누락을 확인합니다.

원본 구현의 반환 규약도 유지합니다. 원본 도구는 성공 또는 오류를 문자열로 반환하는
경우가 있으므로 MCP `isError`만으로 성공 여부를 판단하지 말고 내용도 확인해야 합니다.
새 `ableton_` 도구는 구조화된 결과와 MCP 오류를 사용합니다. 장치/음원/Pack 로딩은
해당 PC에 설치되고 Live Browser에서 사용 가능한 콘텐츠에 한정됩니다.

## 함께 쓰는 방식

| 항목 | 원본 도구 | 추가 도구 |
| --- | --- | --- |
| 이름 | `get_session_info`, `create_clip` 등 원래 이름 | `ableton_` 접두어 |
| 선택 | 0부터 시작하는 track_index / clip_index / device_index | 조회에서 받은 track_id / clip_id 및 note_id |
| 클립 시간 | 원본 도구 설명 유지 | Arrangement는 song beats, 노트는 clip-local beats |
| 저장 | 원본과 동일하게 명시된 동작만 수행 | 자동 Set 저장 없음 |
| 네트워크 | `upstream.` 명령으로 통합 bridge 사용 | 직접 통합 bridge 사용 |

기존 `create_audio_clip`은 **Session 슬롯**에 가져옵니다.
`ableton_create_arrangement_audio_clip`은 **Arrangement 타임라인**에 가져옵니다.
기존 `delete_clip`은 Session 클립 삭제이고 `ableton_delete_arrangement_clip`은
Arrangement 클립 삭제입니다. 기존 `duplicate_to_arrangement`도 그대로 유지됩니다.

원본 현재 main에 일부 Arrangement 기능이 추가되어 있음을 확인했습니다. 사용자의
다른 PC에 설치된 버전은 확인하지 못했으므로 최신 고정 commit 전체를 통합 기준으로
삼았습니다. 이전 실행파일/Remote Script의 wire protocol과는 호환되지 않으며 양쪽을
함께 교체해야 합니다. [전환 절차](setup.md)를 따르세요.

## 선택적 데이터셋/Telemetry

음악 제어와 무관한 원본 6개 도구도 남겼습니다: `set_dataset_consent`, `submit_intent`,
`rate_last_action`, `prefer_candidate`, `reject_last_action`, `record_audition`.
원본의 수집 decorator·동의 확인·기록 로직을 보존하되 **기본 수집/업로드는 꺼짐**입니다.
외부 서비스 계정·키는 포함하지 않으며, 이 작업 중 어떤 데이터도 업로드하지 않았습니다.

기본값은 `ABLETON_MCP_DISABLE_TELEMETRY=true`, `ABLETON_MCP_DISABLE_DATASET=true`입니다.
해당 도구들은 비활성 상태를 반환하거나 로컬 동의만 기록하며, 음악 도구는 정상
사용할 수 있습니다. 로컬 UUID/동의 파일 위치는 bridge 설정 폴더의 `upstream/`
(표준 설치에서는 `doc/local/upstream/`)으로 고정하며 전역 사용자 메모리를 쓰지 않습니다.

원본의 데이터셋 워크플로를 운영하려면 별도의 명시적 설정이 필요합니다:

1. `python -m pip install '.[dataset]'`로 선택 의존성을 설치합니다.
2. 원본의 dataset/telemetry 테이블 및 RLS를 갖춘 자신의 Supabase backend를
   준비합니다. [고정 원본 저장소](https://github.com/ahujasid/ableton-mcp/tree/9dddc7bd5b95412510fdeb745949e3bf23f3fd8a)의
   스키마와 운영 안내를 사용합니다. 이 저장소는 backend 배포를 수행하지 않습니다.
3. MCP 실행 환경에서 `ABLETONCTRL_ENABLE_COLLECTION=true`,
   `ABLETON_MCP_DISABLE_TELEMETRY=false`, `ABLETON_MCP_DISABLE_DATASET=false`와
   자신의 `ABLETON_MCP_SUPABASE_URL`, `ABLETON_MCP_SUPABASE_ANON_KEY`를 설정합니다.
   서버를 재시작한 뒤 원본 도구의 설명대로 사용자 동의를 받습니다. 동의를 추정하지 않습니다.
4. Live UI 이벤트까지 수집하려면 `doc/local/bridge.json`에
   `"capture_passive_events": true`를 넣고 설치 도우미 `--replace`로 동기화한 뒤 Live를
   재시작합니다. 기본값 false에서는 해당 이벤트 capability를 광고하지 않습니다.

이 선택적 설정은 prompt/MIDI/장치 상태 등 원본이 정의한 데이터를 지정 backend에
보냅니다. 개인정보·토큰은 커밋하지 않습니다. 실제 backend 업로드와 Live 수집은
이번 검증에 포함되지 않습니다. 새 Arrangement 도구의 실행은 원본 dataset action
분류에 별도 추가하지 않았으며, 원본 snapshot에서 현재 Arrangement 상태를 조회할 수 있습니다.
