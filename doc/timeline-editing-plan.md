# Timeline editing extension — 2026-09-24

User requested implementation of the omitted trimming/resizing and cross-track copy.
The earlier exclusion was a conservative implementation boundary, not proof that
these operations are impossible. Existing authorization covers implementation.

## Design

- Preserve upstream 37 tools. Add explicit copy/trim/resize tools; extend move with
  an optional target track. Native duplication targets matching MIDI/audio tracks.
- Stage timeline edits in unused space beyond existing content. Temporary copies
  are muted. Validate native positions/lengths before deleting the original.
- Trim edges with disposable MIDI clips or a silent Session audio clip. Never
  duplicate an Arrangement source into an occupied destination.
- Unlooped resizing adjusts content markers on a staging copy and verifies actual
  length. Unwarped audio uses its observed seconds/beat ratio and verifies placement;
  file-boundary clamping is a failure, never reported as exact success.
- Looped extension produces contiguous native-copy segments with phase-adjusted
  start markers, avoiding note/audio re-creation and preserving native clip data.
  Response returns all resulting clip IDs. Limit to 64 output segments per call.
- Keep a full original backup until final placement succeeds. On partial failure
  retain recovery copies and report their handles; no automatic global Undo.
- Audio trimming may use an empty Session slot or a temporary appended scene.
  Generate silence.wav during installation; remove only resources owned by the edit.
- Each edit is one Live Undo step. Verify wrong type/overlap/recording/Freeze before
  mutation. Main-thread access and authenticated loopback are unchanged.

## Research

Official Track/Clip LOM documents native duplicate/delete/create and writable
loop/content markers, while Arrangement start_time/end_time are read-only.
https://docs.cycling74.com/apiref/lom/track/
https://docs.cycling74.com/apiref/lom/clip/

Producer Pal's author-maintained Arrangement-Operations.md reports edge-overlap
trimming, looped-length limits and occupied-target duplication hazards. These are
implementation reports, not Ableton guarantees. Our Python implementation is
written independently; no GPL source is incorporated. Source and exact inspected
revision are recorded in research.md. Native Live 12 verification remains required.

## Validation plan

Stateful fake-native tests: MIDI/audio cross-track copy; mismatch and overlaps;
left/right trim with neighbors; unlooped expansion on both ends; loop phase across
partial periods; unwarped units/file limits; ignored native setters; source deletion
or final placement failure; owned resource cleanup; upstream schema parity and
same-connection stdio integration; wheel installation and silence asset creation.
Finish with independent review, docs/records, commit and push.

## Execution record

Implemented all three tools and cross-track move, 0.3.0 distribution and usage docs.
Initial missing-operation tests failed before implementation. 48 total tests now pass,
including 19 timeline tests. Independent review's holding-area overlap, loop-intro loss
and temporary-cover tracking issues were reproduced and fixed; reviewer confirmed no
open code blockers. Live acceptance remains explicitly pending. Packaging evidence is
recorded in verification.md; Git history records delivery.
