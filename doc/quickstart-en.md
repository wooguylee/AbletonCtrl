# English quickstart

AbletonCtrl 0.3 combines all 37 tools from the pinned ahujasid/ableton-mcp with 17
additional Arrangement tools. One stdio MCP server, one Live Remote Script.
Target: Live 12 Suite. External Python >=3.10; Python 3.12 is recommended for the
verified setup. Windows Live 12.4.6 Suite, automated tests and wheel installation
are verified; macOS acceptance remains pending. For a ready-to-copy Codex setup
request on another computer, see [the handoff guide](other-pc-codex.md).

## Windows

```powershell
git clone https://github.com/wooguylee/AbletonCtrl.git
cd AbletonCtrl
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install .
.venv\Scripts\python scripts\configure.py --user-library 'D:\Ableton\User Library'
```

## macOS

```sh
git clone https://github.com/wooguylee/AbletonCtrl.git
cd AbletonCtrl
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/python scripts/configure.py --user-library "$HOME/Music/Ableton/User Library"
```

Use your actual User Library location from Live Settings > Library. Do not pip
install a `Live` package: the native API is supplied by Live itself.

1. Restart Live. Select **AbletonVVoori** in Settings > Link, Tempo & MIDI >
   Control Surface. MIDI Input/Output may be None.
2. When migrating, deselect the old **AbletonMCP** control surface and remove its
   old MCP client entry. The new authenticated protocol does not connect to the
   original Remote Script on port 9877.
3. Merge `doc/local/codex-config.toml` into your Codex configuration, or merge
   `doc/local/mcp-client.json` into another stdio MCP client's configuration.
   Generated paths are absolute. Never overwrite unrelated settings.
4. Restart/reload your MCP client. Expect **54 tools**. Call `ableton_status` and
   `get_remote_script_info` before attempting edits.
5. Test on a disposable Set, using the acceptance list in [verification](verification.md).

Both the MCP process and Live run on the **same computer**. To install on another
computer, clone and configure there; do not copy `.venv` or `doc/local` tokens.
The installer does not alter your global Codex configuration.

## Install directly from Git

A source checkout is optional. The wheel contains the complete Live Remote Script:

```powershell
mkdir AbletonCtrl
cd AbletonCtrl
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install 'git+https://github.com/wooguylee/AbletonCtrl.git@main'
.venv\Scripts\abletonctrl-install --project-dir . --user-library 'D:\Ableton\User Library'
.venv\Scripts\abletonctrl --config '.\doc\local\bridge.json' --check
```

For a reproducible version, replace `main` with a reviewed commit SHA. With `uv`,
use `uv venv` and `uv pip install 'git+https://github.com/wooguylee/AbletonCtrl.git@main'`,
then the same environment's installer. A persistent environment keeps the generated
Python path stable. The old `ableton-arrangement-mcp` executable remains an alias.

## Update

Close Live, pull the checkout, reinstall with `python -m pip install .`, and run
the installer again with the same User Library plus `--replace`. It backs up the
installed folder to `doc/local/backups`, preserves the token, and refreshes both
connection files. Version 0.3 also generates `silence.wav` in the installed script
folder for audio edge trimming; updating only the MCP package is insufficient.
Restart Live and your MCP client. Do not mix script/server versions.

The Control Surface is now named **AbletonVVoori**. For installations using the old
`AbletonArrangementMCP` folder, close Live, rename that folder to `AbletonVVoori`,
then update with `--replace`. Select only the new surface to avoid a port conflict.

## Scope

Original tool names, parameter schemas and return conventions are retained.
New `ableton_` tools use opaque track/clip handles; original tools use indices.
Arrangement supports MIDI creation, audio import, same/cross-track copy and move,
timeline trim/resize, metadata, deletion and MIDI note read/add/update/delete.
Copies/moves require matching MIDI/audio tracks and free destinations. Audio import
is restricted to the track's free tail. Automation/comping editing and automatic
Set saving are not exposed.

`ableton_trim_arrangement_clip(clip_id, start_beats, end_beats)` keeps a range
inside the original. `ableton_resize_arrangement_clip` accepts either/both absolute
boundaries, preserving the content timeline rather than stretching it. Looped
extensions return up to 64 contiguous native segments with continuous phase,
including any intro before the loop. Both return `clips[]` with new IDs.
`ableton_copy_arrangement_clip` takes `target_track_id` and `destination_beats`;
move accepts an optional target track too. See [examples and recovery](timeline-editing.md).

Timeline edits prepare muted copies beyond the requested range, then keep a full
backup until replacement succeeds. Other clips cannot overlap the requested range.
Unwarped audio cannot extend beyond its file; native length/marker readback is
checked. `PARTIAL_EDIT` or a timeout requires inspection of the clip list/recovery
copies, or manual Live Undo; never blindly retry. Windows Live 12.4.6 Suite was
verified with all 54 tools and MIDI/warped/unwarped Arrangement scenarios. See the
[live report](live-verification-2026-09-25.md). Native automation preservation,
tempo automation, macOS and hosted dataset upload remain unverified.

Unwarped resizing can wait for a later Live tick and span multiple Undo steps
(two observed; the first Undo can restore muted staging clips). Keep Live UI idle
during edits. Deferred resizing of clips with envelopes is rejected.
`create_locator` renames an existing locator or creates the first one only; create
additional locators in Live. This prevents Live's grid-snapped toggle from deleting
an existing locator. The first locator's actual position may be quantized.

Dataset/telemetry tools are optional and off by default. Music control requires
no hosted backend or OpenAI API key. See [compatibility](compatibility.md) for the
precise baseline and optional collection setup; [tools](tools.md) for examples.
