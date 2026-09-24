# English quickstart

AbletonCtrl combines all 37 tools from the pinned ahujasid/ableton-mcp with 14
additional Arrangement tools. One stdio MCP server, one Live Remote Script.
Target: Live 12 Suite. External Python >=3.10; Python 3.12 is recommended for the
verified setup. Windows automated tests and wheel installation are verified;
actual Live and macOS acceptance are still pending.

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

1. Restart Live. Select **AbletonArrangementMCP** in Settings > Link, Tempo & MIDI >
   Control Surface. MIDI Input/Output may be None.
2. When migrating, deselect the old **AbletonMCP** control surface and remove its
   old MCP client entry. The new authenticated protocol does not connect to the
   original Remote Script on port 9877.
3. Merge `doc/local/codex-config.toml` into your Codex configuration, or merge
   `doc/local/mcp-client.json` into another stdio MCP client's configuration.
   Generated paths are absolute. Never overwrite unrelated settings.
4. Restart/reload your MCP client. Expect **51 tools**. Call `ableton_status` and
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
connection files. Restart Live and your MCP client. Do not mix script/server versions.

## Scope

Original tool names, parameter schemas and return conventions are retained.
New `ableton_` tools use opaque track/clip handles; original tools use indices.
Arrangement supports MIDI creation, audio import, copy/move/delete, metadata,
and MIDI note read/add/update/delete. Move requires a free, non-overlapping range
on the same track and returns a new handle. Audio import is restricted to the
track's free tail. Arbitrary timeline trimming/resizing, cross-track Arrangement
copy, automation/comping, and automatic Set saving are not exposed.

Dataset/telemetry tools are optional and off by default. Music control requires
no hosted backend or OpenAI API key. See [compatibility](compatibility.md) for the
precise baseline and optional collection setup; [tools](tools.md) for examples.
