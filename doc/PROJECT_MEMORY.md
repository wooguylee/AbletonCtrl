# Project memory

## User decisions (2026-09-24)
- All project discussions, related information, and project memory go under `doc/`.
- Research and implement a reusable basic MCP for Arrangement clips.
- The user confirmed **Ableton Live 12 Suite**.
- User requested implementation, so proceed through ordinary reversible coding and testing.

## Design
- Python MCP over stdio -> authenticated loopback JSON/TCP -> Live Remote Script.
- Remote Script uses Python standard library only and polls nonblocking sockets in `update_display`.
- All Live reads/writes execute on that callback's main thread.
- Read/list, create MIDI Arrangement clips, duplicate, delete, edit metadata, read/add MIDI notes.
- Arrangement timing is beats, zero at 1.1.1. Clip-local note time is a separate coordinate system.
- No direct start/end assignment, UI automation, `.als` rewriting, automatic retries, or implicit save.
- Public LOM documentation describes Max for Live; Python signatures need runtime validation.

## Environment
- Workspace started empty, with no Git repository or applicable ancestor AGENTS.md.
- Python 3.12.10 is available via `py -3.12`.
- No running Ableton process was detected during initial inspection.
- See `verification.md` for final checks and the remaining Live acceptance steps.

## Delivered state
- 10 MCP tools implemented; `.venv` contains MCP SDK 1.30.0.
- 20 automated tests pass, including a real MCP stdio client and real loopback TCP.
- Config and per-machine client examples generated in `doc/local/`; keep tokens private.
- Remote Script has NOT been installed into a User Library; Live has NOT been controlled yet.
- `--check` currently returns BRIDGE_UNAVAILABLE. Next integration step is the actual
  User Library path, Control Surface activation, and disposable-Set checks in `verification.md`.
- Exported visible user/assistant messages into `doc/conversations/*-visible.jsonl`.
  Refresh the export at task end; app-managed session logs stay in the app's own storage.
- Independent review findings fixed: failed installer updates preserve existing local
  connection settings; transcript metadata removal preserves following user content.
- Native version-sensitive APIs remain capability-checked and live acceptance is outstanding.

## Git workflow (user instruction, 2026-09-24)
- Remote: `origin` = `https://github.com/wooguylee/AbletonCtrl.git`.
- The remote was empty when first checked; initial branch is `main`.
- Finish each completed task with appropriate checks, project record updates,
  a Git commit, and a push. This is authorized; do not ask again for routine completion.
- Never force-push or discard remote history. Verify push and working-tree status.
- `doc/local/`, raw conversation JSONL, `.venv/`, and machine-local `.codex/`
  remain excluded; reviewed Markdown records and source are committed.
