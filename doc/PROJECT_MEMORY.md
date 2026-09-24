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

## Current implementation (0.2.0)

- 51 tools: 37 upstream tools with unchanged input schemas + 14 extended Arrangement tools.
- Upstream pinned to `9dddc7bd5b95412510fdeb745949e3bf23f3fd8a`; MCP 1.4.5,
  Live script 1.7.1. Current upstream already has some Arrangement operations;
  the user's installed older version was not inspected directly.
- Vendor original tool/Live handler code with MIT license. Hash inventory in
  `upstream-source.json`, tool inventory in `upstream-tools.json`.
- stdio MCP → authenticated loopback TCP → combined Remote Script main-thread dispatch.
  No original TCP server; no arbitrary Python. Both reads and writes stay on Live's thread.
- Legacy tools use indices and original string results/errors. New `ableton_` tools
  use current-connection handles and structured responses/errors.
- New Arrangement: list/get, metadata, MIDI create, audio import, duplicate/move/delete,
  MIDI note read/add/update/delete by ID.
- Move is verified copy then source deletion in one Undo step, free same-track range
  only. New ID returned. Partial failures require inspection, no automatic retry/Undo.
- Audio import allowed only at/after last track clip because length depends on Live.
- No arbitrary timeline trimming/resizing, cross-track Arrangement copy, comping,
  automation editing, or automatic Set saving.
- Upstream optional dataset tools/decorators retained, collection off by default;
  backend credentials never bundled. Local state belongs in `doc/local/upstream`.
  Passive capture is opt-in and capability must not be advertised when disabled.

## Distribution / environment

- Windows Python 3.12.10, MCP SDK 1.30.0. No running/controlled Live here.
- Package `ableton-arrangement-mcp` 0.2.0; `abletonctrl` and old executable alias.
- Wheel bundles complete Live script; `abletonctrl-install` or `scripts/configure.py`
  configures explicit User Library. Script folder stays `AbletonArrangementMCP`.
- Installer uses its executing Python, never an unrelated target project's .venv.
- Config examples/token in `doc/local`; generated Codex timeout 180 seconds.
- Switch both the old MCP client entry and old Live control surface together.
- 29 unittest tests pass, including actual stdio/TCP with fake Live native objects.
  Separate venv wheel installation, native file hash parity and 51-tool discovery pass.
- No real User Library installation/native Live acceptance, macOS acceptance or
  optional backend upload test yet. Do not claim those were verified.
- Read `verification.md`, `setup.md`, `compatibility.md` for current instructions.

## Records

- `doc/local/`, `.venv/`, `.codex/`, raw transcript JSONL and credentials are ignored.
- Refresh visible conversation export at task end with `scripts/export_conversation.py`.
  It copies visible user/assistant text; app-managed original session storage is separate.
- Independent review findings (passive capability and interpreter selection) fixed
  and verified. Future changes must keep those regressions covered.
