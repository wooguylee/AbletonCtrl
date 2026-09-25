# 토니 실곡 제작 검증 — 함께 빛으로 / 2026-09-25

## 작업 범위

사용자가 요청한 오리지널 K-POP + EDM + CCM 응원가를 현재 Ableton Live Set의 Arrangement에 토니 MCP로 작성했다. 연결 전 읽기 확인에서 Live 12.4.6 / AbletonCtrl 0.3.1, 정지 상태, 120 BPM, 빈 기본 트랙 4개, Arrangement 클립 0개를 확인했다. 빈 Set이므로 기존 내용을 건드리지 않고 네 기본 트랙은 보존했다.

## 작성 결과

- 템포 128 BPM, 4/4. 시간 변경 없음.
- 9개 신규 MIDI 트랙, 114 Arrangement 클립, 4,290 MIDI 노트.
- 본편은 beat 0–512, 즉 128마디이며 beat 512가 129마디 시작/4:00 경계다.
- 모든 주 편곡 트랙의 클립·노트를 MCP로 다시 조회했다. 구간 경계는 마디 단위이며, 메인 패드·피아노·플럭은 0–512 전체를 연결한다.
- 첫 후렴 핵심 8마디는 bar 33–40 / beat 128–160에 우선 작성한 뒤 전체 구조를 확장했다.
- 클립 이름/색상과 Chorus 1 핵심 클립을 다시 읽어 확인했다.
- 네 기본 트랙은 여전히 Arrangement 클립이 없고 장치도 없다.

## 트랙/장치 및 레이어

MIDI 트랙: 킥·클랩·햇(505 Core Kit Drum Rack), 베이스(Basic Jupo Bass), 몽환 패드(After Glow Pad + Hybrid Reverb), 피아노(E-Piano MKI Mellow), 업비트 플럭(Echo Pulse + Reverb + Echo), 드롭 리드(Euphoria Lead), Vocal Guide MIDI(Basic Sine Drive Lead), 반짝임 벨(Echo Bells + Reverb), 전환 FX MIDI(Drifting Interferences).

벌스 화성은 Bm7–Gadd9–Dadd9–Asus 계열, 후렴은 D–A/C#–Bm7–Gadd9 및 연결 보이싱 변주다. 후렴 킥은 4분음표, 스네어/클랩은 2·4박, 하이햇은 8분음표다. 베이스·플럭·피아노에는 서로 다른 업비트/당김 리듬을 사용했다. 브리지는 킥/베이스를 비우고 피아노·패드 중심으로 만들었다. 마지막 후렴은 서로 다른 8마디 블록 3개로 밀도를 올렸다.

4행 후렴 가사와 전체 구간 안내는 Git 제외 폴더 `songs/함께 빛으로/곡 자료와 가사.md`에 있다. Vocal Guide MIDI 음역은 재조회 후 D4–D5로 맞췄다. 실제 보컬 음성은 생성하지 않았다.

## 제약 및 다음 단계

MCP에는 Live Set 저장, 오디오 렌더링, 자동 청취 기능이 없다. 현재 편곡은 Live 메모리에 있으며 사용자가 `songs/함께 빛으로/함께 빛으로.als`로 Save As 해야 한다. 이후 전체 1.1.1–129.1.1 경계를 선택해 Audio/Video Export를 수동 실행할 수 있다. 실제 음색/밸런스/가사 싱크는 청취 검수가 남아 있다.

Live의 현재 상태 조회에서 `전환 FX · MIDI` 트랙이 Arm 상태로 보고됐다. 이 버전 MCP에는 Arm 해제 도구가 없어 재생 전 Live에서 수동으로 Arm을 끈다. Live 재생/화면 자동화는 수행하지 않았다.

## 조회 증거

- 연결/Set 읽기 전용 응답: `doc/local/live-acceptance-20260925-164757.json`
- 전체 Track/Arrangement clip/MIDI note 조회: Live 12.4.6, 128 BPM, 13 tracks(기본 4 + 신규 9), 114 clips, 4,290 notes; 각 노트 포함 클립 0/512 beat 경계 확인.
- 장치 재조회: 패드 Hybrid Reverb, 플럭 Reverb/Echo, 벨 Reverb 확인.
- Git 대상에는 이 요약/대화 기록만 포함한다. `songs/`는 `.gitignore`로 제외된다.
