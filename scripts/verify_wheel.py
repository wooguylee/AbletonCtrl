"""Run with an isolated wheel-installed Python, from any working directory."""
import asyncio
import hashlib
import json
import sys
import tempfile
import wave
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import ableton_arrangement_mcp
from ableton_arrangement_mcp.installer import configure

ROOT = Path(__file__).resolve().parents[1]


async def check():
    package = Path(ableton_arrangement_mcp.__file__).resolve()
    assert "site-packages" in package.parts, package
    with tempfile.TemporaryDirectory(dir=ROOT / "doc/local", prefix="wheel-smoke-") as directory:
        project, library = Path(directory) / "Project", Path(directory) / "User Library"
        library.mkdir()
        config, target = configure(project, library)
        for source in (ROOT / "remote_script/AbletonArrangementMCP").glob("*.py"):
            assert hashlib.sha256(source.read_bytes()).digest() == hashlib.sha256((target/source.name).read_bytes()).digest(), source.name
        assert (target / "LICENSE").is_file()
        with wave.open(str(target / "silence.wav")) as silent:
            assert silent.getnframes() == 22050
            assert not any(silent.readframes(22050))
        assert config.read_bytes() == (target / "config.json").read_bytes()
        generated = json.loads((config.parent / "mcp-client.json").read_text())["mcpServers"]["abletonctrl"]
        assert generated["command"] == sys.executable
        params = StdioServerParameters(**generated, cwd=str(project))
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listing = await session.list_tools()
                assert len(listing.tools) == 54
                names = {tool.name for tool in listing.tools}
                assert {"create_clip", "load_drum_kit", "ableton_move_arrangement_clip",
                        "ableton_copy_arrangement_clip", "ableton_trim_arrangement_clip",
                        "ableton_resize_arrangement_clip"} <= names
    print("Wheel smoke OK: installed package, bundled script hashes, generated silence WAV, local configuration, real stdio discovery (54 tools)")


if __name__ == "__main__":
    asyncio.run(check())
