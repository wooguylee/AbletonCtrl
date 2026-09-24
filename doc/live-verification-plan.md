# Live 12.4.6 acceptance and debugging

User authorized real Live testing after activating AbletonVVoori. Use the saved disposable Set under doc/local. Original four empty tracks must remain unchanged.

- Verify all 54 MCP tool routes with native Live results. Dataset collection stays off.
- Mandatory Arrangement matrix: MIDI/audio, looped/unlooped, Warp on/off; copy/move between tracks, trim/resize, note IDs, metadata and overlap guards.
- Reproduced: unwarped loop markers change but Arrangement end_time remains stale inside one callback; determine whether next Live tick commits length before designing the fix.
- Reproduced: original create_locator sets cue at previous playhead (0 or 216), not requested 0.25/4, when positioning and cue creation share a callback. Preserve vendor source and fix adapter if needed.
- If deferred updates are confirmed, use bounded main-thread continuation with serialized bridge requests. Never sleep/block Live or read its API on a worker thread. Preserve Undo and cleanup on cancellation.
- Verify Undo/Redo, original track preservation, wheel parity, unit/stdio suite. Update reusable test instructions and commit/push.

Completed: final native 54 tools / 93 calls, 61 automatic tests, original four tracks unchanged, isolated wheel verified. See live-verification-2026-09-25.md for actual limits and evidence.
