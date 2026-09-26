# 함께 빛으로 — 16번 악기 교체 (2026-09-27)

사용자는 16번 트랙의 소리가 느리게 밀리는 느낌을 지적하고, 정박에 바로 들어가면서
몽환적인 느낌을 유지할 악기를 선택하도록 요청했다.

## 확인과 선택

실제 Live의 16번(0-based index 15)은 `빛 | 함께 부르는 패드`였으며
Morning Chorus Pad(Drift) → Reverb → Utility 체인이었다. 89–96, 105–112,
113–120마디의 3클립/96개 MIDI 노트는 모두 마디 첫 박에 시작한다.
기존 Env 1 Attack은 0.34126985, Env 2 Attack은 0.45238096이었다.
이 수치는 native normalized parameter 값이며 밀리초가 아니다. MIDI 배치가 아닌
느린 엔벌로프 상승이 늦게 들리는 원인의 유력한 후보다. 오디오로 직접 확인하지는 않았다.

설치된 `instruments/Drift/Synth Keys`를 MCP로 조회한 후 **Gentle Sixty.adv**를 선택했다.
지원되는 load_instrument_or_effect로 16번의 기존 악기를 교체하고, 실제 체인이
Gentle Sixty → Reverb → Utility로 유지되는지 확인했다.

## 적용한 음색

- Env 1/2 Attack을 각각 0.02로 줄여 빠른 음량/필터 반응으로 구성했다.
- Env 1 Sustain 0.65, Env 1/2 Release 0.30으로 부드러운 유지음과 정리된 끝음을 설정했다.
- LP Freq 0.58, Spread 0.60, Drift 0.10으로 따뜻한 음색과 넓은 공간감을 구성했다.
- 필터·피치·매트릭스 변조량을 중립값으로 설정하고 Glide Time=0, Env 2 Cyc On=0으로
  시작이 흐려지는 움직임을 줄였다. Noise Gain=0.12로 잡음 층을 낮췄다.
- Osc 1 Oct=0, Transpose=12, Volume=0.31746033으로 기존 주요 음역/출력 기준을 유지했다.
- 기존 Reverb Dry/Wet 0.30 및 Utility Stereo Width 1.20/Output -0.27을 그대로 보존했다.

이펙트의 잔향으로 몽환감을 유지하고, 악기의 직접음이 먼저 시작하도록 한 선택이다.
위의 값은 모두 실제 장치의 native 값이며 ms/dB로 임의 환산하지 않았다.

## 검증과 보관

변경한 22개 파라미터를 다시 읽어 설정값과 대조했다. 3클립/96음표의 모든 조회 필드가
수정 전과 완전히 동일하다. 다른 17개 트랙의 snapshot, 16번의 Reverb/Utility,
믹서/Session 슬롯/클립 배치, transport/return/master/cue/scenes도 변경 전후 일치했다.
실제 청취, Set 저장/오디오 렌더링, 화면 자동화는 하지 않았다.

작업 자료와 복구용 기존 값은 Git 제외
`songs/함께 빛으로/2026-09-25 새 편곡/2026-09-27 16번 악기/`에 보관했다.
곡 폴더의 instruments.json, verification.json, final-snapshot.json 및 곡 안내를 갱신했다.
MIDI는 변경하지 않아 다시 내보내지 않았다.

청취 지점은 **2:45(89마디)**와 **3:15(105마디)**다. 사용자는 Live에서 이 구간의
첫 박 어택과 잔향을 확인하고 변경된 Set을 수동 저장한다.
