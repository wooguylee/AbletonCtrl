# Upstream compatibility integration — 2026-09-24

## Corrected requirement
The user's other PC already uses `ahujasid/ableton-mcp`. AbletonCtrl must retain
that MCP's full tool surface and add Arrangement editing, in one distributable
repository and one configured MCP server. Finish with commit/push. Source and
knowledge remain in this project; operational records stay under `doc/`.

## Baseline and design
- Pin upstream commit `9dddc7bd5b95412510fdeb745949e3bf23f3fd8a`, package 1.4.5,
  Live script 1.7.1. Its current main already contains some Arrangement tools;
  the user's installed older version is not available for direct comparison.
- Vendor the original tool implementations and Live handlers with MIT notices.
  Preserve all upstream public names, parameters/defaults and return conventions.
- Register those tools alongside the existing Arrangement tools in one FastMCP.
- Route both sets through the authenticated local bridge and Live main-thread
  dispatch. Do not run the original unauthenticated socket server or schedule a
  callback and block the same Live thread waiting for that callback.
- Preserve optional upstream dataset tool implementations, default collection off;
  project-local state only. Music control never requires a telemetry backend.
- Bundle the complete combined Live script in the Python wheel and expose an
  installer entry point, so Git/pip/uv installation does not need a second repo.
- Add audio Arrangement import, guarded same-track move, and MIDI note ID editing
  and deletion where the runtime supports them. Do not pretend timeline end/start
  setters exist; document public API limitations.

## Tasks and evidence
- [x] Capture upstream tool schema inventory, source hashes and licensing.
- [x] Add failing parity tests and one-MCP old/new integration tests.
- [x] Implement vendor adapter and combined Live main-thread dispatch.
- [x] Expand Arrangement operations with focused state-transition tests.
- [x] Package/install test from a built wheel outside the source checkout.
- [x] Korean/English quickstart, migration, parity table and live acceptance docs.
- [x] Independent review and required checks. Commit/push and remote verification follow as the final completion step.

No Live instance is available here. Protocol/fake-Live/wheel checks must be
reported separately from real-device acceptance; no claim of native success.
