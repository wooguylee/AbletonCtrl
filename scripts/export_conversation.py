"""Copy visible messages from an explicitly selected Codex JSONL session into doc/."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def export_session(session, output):
    messages = []
    source = Path(session)
    # response_item messages are authoritative; event_msg duplicates are excluded.
    with source.open(encoding="utf-8") as file:
        for line in file:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue  # A live log may end with an unfinished line.
            payload = record.get("payload", {})
            if record.get("type") != "response_item" or payload.get("type") != "message":
                continue
            role = payload.get("role")
            if role not in ("user", "assistant") or payload.get("channel") == "analysis":
                continue
            content = payload.get("content", [])
            parts = [part.get("text", "") for part in content
                     if isinstance(part, dict) and part.get("type") in ("input_text", "output_text", "text")]
            text = "\n".join(parts)
            while True:
                stripped = re.sub(r"^\s*<(recommended_plugins|environment_context)>.*?</\1>\s*", "", text,
                                  count=1, flags=re.DOTALL)
                if stripped == text:
                    break
                text = stripped
            if not text:
                continue
            messages.append({"timestamp": record.get("timestamp"), "role": role,
                             "channel": payload.get("channel"), "text": text})
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(m, ensure_ascii=False) + "\n" for m in messages), encoding="utf-8")
    return len(messages)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, type=Path, help="Exact JSONL session path; no global auto-scan")
    args = parser.parse_args()
    output = ROOT / "doc" / "conversations" / (args.session.stem + "-visible.jsonl")
    count = export_session(args.session, output)
    print("Exported %s visible messages to %s" % (count, output))


if __name__ == "__main__":
    main()
