# AbletonCtrl

## Project nickname
AbletonVVoori의 별명은 **토니**입니다. 사용자가 "토니"라고 하면 이 프로젝트의
AbletonVVoori / AbletonCtrl MCP를 뜻합니다. Control Surface 표시 이름은
`AbletonVVoori`, MCP 등록 이름은 `abletonctrl`을 유지합니다.

Read `doc/PROJECT_MEMORY.md` and `doc/README.md` before working here.
All project conversation records, research, plans, verification reports, and
project memory belong under this project's `doc/` directory. Update them at
the end of each task. Do not save this project's memory in a global memory store.
Keep user/assistant conversation text in `doc/conversations/`; clearly label
summaries. Do not include hidden instructions, credentials, or private reasoning.
Use `scripts/export_conversation.py` for an available Codex session transcript.
The app's own storage is separate and cannot be relocated by these instructions.

Target Ableton Live 12 Suite. Live API access must stay on the Live main thread.
Never test writes against a user's active Set without authorization. Use the
fake Live integration tests and document what still requires live verification.
Keep the bridge bound to loopback; do not execute arbitrary Python/API methods.

## Song storage
Save every created or edited song under `songs/<song title>/`, with a separate
directory for each song. The entire root `songs/` directory is Git-ignored.
Keep Live projects/Sets, MIDI/audio exports and song working files there; never
force-add them to Git. Keep project-level summaries and verification records in
`doc/`. Use MCP for music editing. Do not start screen automation implicitly;
the 2026-09-25 UI permission covered saving that song only.

## Git completion
The user requires completed work to end with a Git commit and push to
`https://github.com/wooguylee/AbletonCtrl.git` (origin).
Run checks appropriate to the change, update the records under `doc/`, inspect
the staged diff for secrets/unrelated files, then commit and push the current
branch. Verify the remote commit and clean working tree before reporting success.
Do not force-push or overwrite remote history. Keep tokens, virtual environments,
machine-local configuration and raw conversation exports out of Git.
