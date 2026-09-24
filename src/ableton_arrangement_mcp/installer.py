"""Generate local connection files, optionally install into an explicit User Library."""
import argparse
import datetime
import json
import secrets
import shutil
import sys
import wave
from pathlib import Path
from importlib.resources import files

SCRIPT_NAME = "AbletonArrangementMCP"


def write_silence(path):
    """Generate a deterministic one-second PCM helper, with no source-media dependency."""
    temporary = path.with_suffix(".wav.tmp")
    with wave.open(str(temporary), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(22050)
        output.writeframes(b"\0" * 44100)
    temporary.replace(path)


def configure(root=None, user_library=None, port=None, replace=False):
    root = Path(root or Path.cwd()).expanduser().resolve()
    local = root / "doc" / "local"
    local.mkdir(parents=True, exist_ok=True)
    config_path = local / "bridge.json"
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {
        "token": secrets.token_hex(32), "port": 8765, "timeout": 10}
    if port is not None:
        if type(port) is not int or not 1024 <= port <= 65535:
            raise ValueError("port must be 1024-65535")
        config["port"] = port
    config_text = json.dumps(config, indent=2) + "\n"
    # This interpreter can import the installer/package; an existing project
    # .venv may belong to an unrelated application and must not be guessed.
    python = Path(sys.executable)
    args = ["-m", "ableton_arrangement_mcp", "--config", str(config_path)]
    client = {"mcpServers": {"abletonctrl": {"command": str(python), "args": args}}}
    toml = ("[mcp_servers.abletonctrl]\ncommand = " + json.dumps(str(python)) +
            "\nargs = " + json.dumps(args) + "\nstartup_timeout_sec = 20\ntool_timeout_sec = 180\n")
    target = None
    if user_library is not None:
        library = Path(user_library).expanduser().resolve(strict=True)
        if not library.is_dir():
            raise ValueError("User Library must be an existing directory")
        target = library / "Remote Scripts" / SCRIPT_NAME
        if target.is_symlink() or not target.resolve().is_relative_to(library):
            raise ValueError("Remote Script destination escapes the User Library")
        if target.exists():
            if not replace:
                raise FileExistsError("Remote Script already exists; use --replace to back up and update it")
            stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            backup = local / "backups" / (SCRIPT_NAME + "-" + stamp)
            shutil.copytree(target, backup)
        source = root / "remote_script" / SCRIPT_NAME
        if not source.is_dir():
            source = Path(str(files("ableton_arrangement_mcp.live_script")))
        shutil.copytree(source, target, dirs_exist_ok=replace,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "config.json"))
        write_silence(target / "silence.wav")
        # Commit connection settings only after destination validation and source copy succeed.
        installed_temp = target / "config.json.tmp"
        installed_temp.write_text(config_text, encoding="utf-8")
        installed_temp.replace(target / "config.json")
    local_temp = config_path.with_suffix(".json.tmp")
    local_temp.write_text(config_text, encoding="utf-8")
    local_temp.replace(config_path)
    (local / "mcp-client.json").write_text(json.dumps(client, indent=2) + "\n", encoding="utf-8")
    (local / "codex-config.toml").write_text(toml, encoding="utf-8")
    return config_path, target


def main(default_root=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=default_root or Path.cwd(),
                        help="Folder in which doc/local connection settings will be stored")
    parser.add_argument("--user-library", help="Exact existing User Library path; omit to generate project config only")
    parser.add_argument("--port", type=int)
    parser.add_argument("--replace", action="store_true", help="Back up an existing bridge under doc/local/backups and overwrite its managed files")
    args = parser.parse_args()
    try:
        config, target = configure(root=args.project_dir, user_library=args.user_library, port=args.port, replace=args.replace)
    except (OSError, ValueError) as exc:
        parser.exit(1, str(exc) + "\n")
    print("Config: %s (token hidden)" % config)
    print("Client examples: %s" % config.parent)
    if target:
        print("Installed: %s\nRestart Live, then select %s as a Control Surface." % (target, SCRIPT_NAME))
    else:
        print("Remote Script not installed. Rerun with --user-library to install.")


if __name__ == "__main__":
    main()
