"""Source-checkout entry point; the wheel ships the same installer implementation."""
from pathlib import Path
from ableton_arrangement_mcp.installer import configure, main

if __name__ == "__main__":
    main(default_root=Path(__file__).resolve().parents[1])
