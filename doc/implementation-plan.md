> Historical 0.1 Arrangement-only plan. Current scope: [upstream integration](upstream-integration-plan.md) and [README](README.md).

# Arrangement MCP implementation plan

**Goal:** reusable basic Arrangement clip MCP for Live 12 Suite.
**Architecture:** stdio MCP -> loopback TCP -> main-thread Live adapter.
**Tech stack:** Python 3.10+ externally, standard-library Python inside Live.
**Spec:** [design.md](design.md)

## Constraints and review focus
All knowledge under `doc/`; no existing Git repository to branch or commit.
Test stale handles, ordering changes, occupied ranges, auth/expiry/framing,
native API failure, and MCP errors. Native Live integration remains unverified
until run inside Live 12 Suite. Do not install into a guessed User Library.

## Tasks
- [x] 1. Write failing behavior tests for `remote_script/AbletonArrangementMCP/api.py`:
  discovery, guarded edits, creation/duplication/deletion, notes, undo cleanup.
- [x] 2. Implement the Live-independent dispatcher and real Remote Script entrypoint.
- [x] 3. Write socket/client tests; implement bounded nonblocking TCP and external client.
- [x] 4. Implement typed MCP tools with SDK annotations and verify real stdio sessions.
- [x] 5. Add portable install/configuration and conversation export helpers.
- [x] 6. Write Korean setup, tool reference, reuse guide, research, and verification report.

Commands: `py -3.12 -m venv .venv`, `.venv\Scripts\python -m pip install -e .`,
`.venv\Scripts\python -m unittest discover -s tests -v`.
Follow test-first development: verify missing behavior fails, then implement and
rerun the relevant tests. Final review checks the entire delivered interface.
