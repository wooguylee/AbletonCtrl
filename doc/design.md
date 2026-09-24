# Arrangement MCP design — 2026-09-24

## Goal and scope
Control Arrangement clips from an MCP client on Ableton Live 12 Suite. Deliver
reusable source, installation instructions, research references, and tests.
Everything written for project knowledge stays below `doc/`.

## Options considered
1. **Remote Script + local MCP (selected):** self-contained Python bridge, no
   device required in each Set. Python Live API/framework compatibility must be
   verified inside the installed Live build.
2. **Max for Live device:** documented Live Object Model access and suitable for
   Suite, but requires a device and additional patch/network lifecycle handling.
3. **Extend AbletonOSC:** useful established transport; existing clip handlers
   select Session clip slots, so Arrangement targeting still needs an extension.

## Architecture
MCP uses the official Python SDK v1. Live gets a standard-library-only Remote
Script. TCP uses one newline-delimited JSON request and response per connection,
request IDs, a shared random token, finite deadlines, bounded messages/clients.
Live never blocks waiting for networking. Every API call runs in `update_display`.
MCP never retries a command after timeout; the result may be unknown.

## Targeting and edits
Lists return opaque bridge-lifetime handles. A handle is resolved against the
current Set and track before use; deleting/reordering clips cannot retarget an
index-based write. Lists are paginated. Creation/duplication refuses occupied
time ranges. Deletion uses an explicit MCP tool with destructive annotations.
Mutations are grouped in a Live undo step; this is not a transaction or rollback.
The basic version allows only name, RGB color, and muted metadata changes.
Notes use `Live.Clip.MidiNoteSpecification`, not Max's JSON dictionary form.

## Validation
Unit tests use a deliberately small fake Live model. Socket tests exercise real
TCP framing, auth, deadlines, disconnects, and JSON errors. An MCP subprocess test
performs initialization, discovery, reads, writes and errors through the actual
stdio SDK client. These prove the bridge contract, not native Live compatibility.
Final live checks use a disposable Set after installation/activation by the user.
