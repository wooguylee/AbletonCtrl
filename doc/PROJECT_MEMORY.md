# Project memory

## User decisions

- All project conversations, research, plans, results, and knowledge stay under this
  project's `doc/`. No global memory writes. On 2026-09-25 the user explicitly requested
  full cross-PC installation/MCP setup instructions in root README, replacing its index-only role.
- Target **Ableton Live 12 Suite**.
- Control Surface / installed Remote Script name: **AbletonVVoori** (user requested).
- Nickname: **토니**. The user explicitly requested this in AGENTS.md on 2026-09-25.
  "토니" refers to this AbletonVVoori / AbletonCtrl MCP; installed and MCP names stay unchanged.
  Songwriting request examples and current capability boundaries are in doc/tony-songwriting.md.
- Requested anthem style: K-POP + EDM + CCM, dreamy and syncopated, 4 minutes.
  doc/tony-anthem-prompt.md is a prompt only (128 BPM, 4/4, 128 bars), not an executed
  song or a change to the user's current Set. The supplied title/key are example choices.
- 2026-09-25: user completed setup and explicitly authorized full native testing,
  especially Arrangement. Tests use dedicated local Sets under doc/local/.
- Preserve **all tools of ahujasid/ableton-mcp** and add Arrangement control in one
  reusable server/script distribution. The initial Arrangement-only design is historical.
- Remote `origin`: `https://github.com/wooguylee/AbletonCtrl.git`, branch `main`.
- Finish authorized work with checks, record updates, commit and push. Do not re-ask.
  Never force-push or discard remote history.
- 2026-09-25: all created/edited songs belong in root `songs/<song title>/`.
  `/songs/` is Git-ignored, including Live Project folders, Sets, MIDI/audio and
  musical working files. Only project documentation/rules are committed.
- Music editing uses MCP. After the user questioned unsolicited screen automation,
  they authorized UI automation **for this save only**. Do not generalize that
  permission to later playback, editing or saving tasks.
- First song: **햇살이 머문 거리** (Sunlit Avenue), 100 BPM, 4/4, A-minor-centered
  city pop instrumental, 80 bars / 192 seconds. Five new tracks, 50 Arrangement
  clips and 3,255 MIDI notes; four original empty tracks preserved. Saved through
  Live's Save As under `songs/햇살이 머문 거리/햇살이 머문 거리 Project/`.
  Read-only saved XML and MIDI checks passed; sound/mix not auditioned.

## Current implementation (0.3.1)

- 54 tools: 37 upstream tools with unchanged input schemas + 17 extended Arrangement tools.
- Upstream pinned to `9dddc7bd5b95412510fdeb745949e3bf23f3fd8a`; MCP 1.4.5,
  Live script 1.7.1. Current upstream already has some Arrangement operations;
  the user's installed older version was not inspected directly.
- Vendor original tool/Live handler code with MIT license. Hash inventory in
  `upstream-source.json`, tool inventory in `upstream-tools.json`.
- stdio MCP → authenticated loopback TCP → combined Remote Script main-thread dispatch.
  No original TCP server; no arbitrary Python. Both reads and writes stay on Live's thread.
- Legacy tools use indices and original string results/errors. New `ableton_` tools
  use current-connection handles and structured responses/errors.
- New Arrangement: list/get, metadata, MIDI create, audio import, same/cross-track
  copy/move/delete, timeline trim/resize, MIDI note read/add/update/delete by ID.
- Move is verified copy then source deletion in one Undo step, free matching-track
  range only. New ID returned. Partial failures require inspection, no automatic retry/Undo.
- Timeline edits prepare muted native copies beyond all content AND requested end,
  verify actual bounds, retain full backup until replacement succeeds. No direct
  start_time/end_time write. Original is excluded from resize overlap checks only.
- Loop extension returns up to 64 contiguous clips, including preserved loop intro
  and phase. Unlooped resize exposes hidden content; unwarped uses observed seconds
  per beat and rejects file overflow. Tempo automation conversion is unverified.
- Audio edge trimming uses installer-generated silence.wav in a temporary Session
  slot/owned appended Scene. Reinstall script on upgrade. PARTIAL_EDIT retains recovery
  copies where possible; inspect or manually Undo. Never retry blindly.
- Audio import allowed only at/after last track clip because length depends on Live.
- No overwrite of other clips, single-clip consolidation of loop extensions, comping,
  automation editing, or automatic Set saving.
- Upstream optional dataset tools/decorators retained, collection off by default;
  backend credentials never bundled. Local state belongs in `doc/local/upstream`.
  Passive capture is opt-in and capability must not be advertised when disabled.

## Distribution / environment

- Windows Python 3.12.10, MCP SDK 1.30.0. Live 12.4.6 Suite installation confirmed.
- Package `ableton-arrangement-mcp` 0.3.1; `abletonctrl` and old executable alias.
- Wheel bundles complete Live script; `abletonctrl-install` or `scripts/configure.py`
  configures explicit User Library. Installed folder is `AbletonVVoori`; source folder
  remains `remote_script/AbletonArrangementMCP` to preserve imports/vendor provenance.
- Installer uses its executing Python, never an unrelated target project's .venv.
- Config examples/token in `doc/local`; generated Codex timeout 180 seconds.
- Switch both the old MCP client entry and old Live control surface together.
- 61 unittest tests pass, including 24 timeline regressions and actual stdio/TCP with
  fake Live native objects. Separate venv wheel installation, native file hash parity,
  generated silence WAV and 54-tool discovery are recorded in verification.md.
- Installed into confirmed `C:/Users/Administrator/Documents/Ableton/User Library`.
  Live 12.4.6 Suite activated AbletonVVoori. All 54 tools exercised through real MCP;
  optional dataset tools checked off, no hosted upload. See live-verification-2026-09-25.md.
  Dedicated Arrangement MIDI/warped/unwarped tests, cross-track copy/move, full Session
  slots and Undo/Redo verified. No macOS/tempo automation/clip envelope acceptance.
- Read `verification.md`, `setup.md`, `compatibility.md` for current instructions.

## Records

- `doc/local/`, `.venv/`, `.codex/`, raw transcript JSONL and credentials are ignored.
- Refresh visible conversation export at task end with `scripts/export_conversation.py`.
  It copies visible user/assistant text; app-managed original session storage is separate.
- Independent review findings (passive capability and interpreter selection) fixed
  and verified. Future changes must keep those regressions covered.
- Timeline review fixed holding/final-range collision, lost loop intro, and untracked
  wrong-length temporary cover. Preserve these regression tests. Native timing and
  Undo now have evidence in live-verification-2026-09-25.md; automation remains unverified.
- Producer Pal behavior research is GPL-source-free independent implementation;
  pinned research provenance is recorded in research.md, no vendor code was added.

## Native findings in 0.3.1

- Unwarped marker length updates next Live tick. Deferred generator runs only on the
  Live main thread; source retained/rechecked before commit. Other MCP calls serialized.
- Keep Live UI idle during edits. Scalar source fingerprint is not a full transaction.
  Existing clip envelopes on a deferred unwarped resize are rejected before yielding.
- Deferred resize Undo/Redo may span multiple steps (two native steps observed).
  First Undo can leave muted staging clips; inspect after success/failure, never auto-Undo.
  Normal MIDI move was verified as one-step Undo/Redo.
- Locator API snaps to editing grid and can DELETE an existing cue even when selected
  predicate is false. Adapter permits near-existing rename or first cue only; any other
  creation returns UNSUPPORTED before mutations, with recheck after deferred tick.
  Actual first-cue time may be quantized. Do not remove this guard based on fake tests.
- 37 upstream tool schemas and vendored original bytes remain unchanged.
- Reusable native runner: scripts/live_acceptance.py (read-only default; --run-writes
  adds 5 test tracks, Drift and Core Library 505 Core Kit). Raw reports/media are local.
- Cross-PC Codex installation handoff: root README.md is the canonical guide;
  doc/other-pc-codex.md points to it. A repository URL plus a request to install
  and configure MCP following README.md provides the task context. Generate local paths/token on the destination PC; merge
  the generated abletonctrl table into user config for use across projects.
  Initial connection verification is read-only; Live and MCP run on the same host.

## 두 번째 곡: 함께 빛으로 (2026-09-25)

### 같은 날 새 빈 Set에서 만든 새 편곡

후속 요청은 별도의 빈 기본 4트랙 Set을 MCP로 확인한 뒤 새 편곡으로 실행했다.
14개 신규 트랙, 163 Arrangement clips, 5,846 notes, 128 BPM/4/4/128마디(beat 0–512).
먼저 33–40마디 핵심 후렴 12클립/518노트를 작성했다. 마지막 후렴은 12→13→14 레이어이며
Vocal Guide는 MIDI 62–74/D major 음계다. 최종 트랙/장치/모든 클립·노트 재조회와 MIDI
백업 파싱을 완료했다. 새 자료는 `songs/함께 빛으로/2026-09-25 새 편곡/`이며 이전 .als는
보존했다. 새 편곡은 Live 메모리에 있으므로 수동 Save As/Export가 필요하다. FX Arm 해제와
청취 검수도 수동이다. 상세: `song-together-light-new-arrangement-2026-09-25.md`.

### 이전 편곡 기록

토니 MCP로 Live 12.4.6의 빈 Set에 128 BPM·4/4·D major 중심 128마디 응원가를 작성했다. 기본 4트랙은 보존하고 9 MIDI 트랙, 114 Arrangement clips, 4,290 notes를 만들었으며 전체 배치와 음표를 재조회했다. 첫 8마디 후렴을 먼저 만든 뒤 변주 블록으로 전개했다. 505 Core Kit, Basic Jupo Bass, After Glow Pad, E-Piano MKI Mellow, Echo Pulse, Euphoria Lead, Basic Sine Drive Lead, Echo Bells, Drifting Interferences와 Live 기본 Reverb/Hybrid Reverb/Echo를 사용했다. Vocal Guide MIDI는 D4–D5로 정리했고 실제 보컬은 생성하지 않았다. Set 저장과 오디오 렌더링은 MCP 범위 밖이므로 사용자가 `songs/함께 빛으로/`에 수동 저장한다. 상세 결과 및 들을 지점은 `song-together-light-2026-09-25.md`, 곡 자료·가사는 Git 제외 폴더를 참고한다.
