# Project memory

## User decisions

- All project conversations, research, plans, results, and knowledge stay under this
  project's `doc/`. No global memory writes. Root README is only a documentation index.
- Target **Ableton Live 12 Suite**.
- Preserve **all tools of ahujasid/ableton-mcp** and add Arrangement control in one
  reusable server/script distribution. The initial Arrangement-only design is historical.
- Remote `origin`: `https://github.com/wooguylee/AbletonCtrl.git`, branch `main`.
- Finish authorized work with checks, record updates, commit and push. Do not re-ask.
  Never force-push or discard remote history.

## Current implementation (0.3.0)

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

- Windows Python 3.12.10, MCP SDK 1.30.0. No running/controlled Live here.
- Package `ableton-arrangement-mcp` 0.3.0; `abletonctrl` and old executable alias.
- Wheel bundles complete Live script; `abletonctrl-install` or `scripts/configure.py`
  configures explicit User Library. Script folder stays `AbletonArrangementMCP`.
- Installer uses its executing Python, never an unrelated target project's .venv.
- Config examples/token in `doc/local`; generated Codex timeout 180 seconds.
- Switch both the old MCP client entry and old Live control surface together.
- 48 unittest tests pass, including 19 timeline regressions and actual stdio/TCP with
  fake Live native objects. Separate venv wheel installation, native file hash parity,
  generated silence WAV and 54-tool discovery are recorded in verification.md.
- No real User Library installation/native Live acceptance, macOS acceptance or
  optional backend upload test yet. Do not claim those were verified.
- Read `verification.md`, `setup.md`, `compatibility.md` for current instructions.

## Records

- `doc/local/`, `.venv/`, `.codex/`, raw transcript JSONL and credentials are ignored.
- Refresh visible conversation export at task end with `scripts/export_conversation.py`.
  It copies visible user/assistant text; app-managed original session storage is separate.
- Independent review findings (passive capability and interpreter selection) fixed
  and verified. Future changes must keep those regressions covered.
- Timeline review fixed holding/final-range collision, lost loop intro, and untracked
  wrong-length temporary cover. Preserve these regression tests. Actual native edge
  object identity, audio warp timing, automation preservation and Undo need Live tests.
- Producer Pal behavior research is GPL-source-free independent implementation;
  pinned research provenance is recorded in research.md, no vendor code was added.
