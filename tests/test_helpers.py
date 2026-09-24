import json
import tempfile
import unittest
from pathlib import Path
from scripts.configure import configure
from scripts.export_conversation import export_session


class HelperTests(unittest.TestCase):
    def test_failed_update_preserves_working_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Project"
            source = root / "remote_script" / "AbletonArrangementMCP"
            source.mkdir(parents=True)
            (source / "__init__.py").write_text("# fake installer source\n", encoding="utf-8")
            library = Path(directory) / "User Library"
            library.mkdir()
            config_path, target = configure(root, library)
            initial = config_path.read_bytes()
            with self.assertRaises(FileExistsError):
                configure(root, library, port=9876)
            self.assertEqual(config_path.read_bytes(), initial)
            self.assertEqual((target / "config.json").read_bytes(), initial)
            with self.assertRaises(FileNotFoundError):
                configure(root, library / "missing", port=9876)
            self.assertEqual(config_path.read_bytes(), initial)
            configure(root, library, port=9876, replace=True)
            self.assertEqual(json.loads(config_path.read_text())["port"], 9876)
            self.assertEqual(config_path.read_bytes(), (target / "config.json").read_bytes())
            self.assertEqual(len(list((root / "doc/local/backups").iterdir())), 1)

    def test_export_keeps_request_after_metadata_and_excludes_hidden_content(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "session.jsonl"
            output = Path(directory) / "visible.jsonl"
            def message(role, text, channel=None):
                return {"type": "response_item", "payload": {"type": "message", "role": role,
                        "channel": channel, "content": [{"type": "input_text", "text": text}]}}
            records = [message("user", "<recommended_plugins>metadata</recommended_plugins>\n<environment_context>env</environment_context>\nPlease implement Arrangement MCP."),
                       message("assistant", "private reasoning", "analysis"),
                       message("developer", "private instructions"),
                       message("assistant", "Visible result", "final")]
            source.write_text("\n".join(json.dumps(r) for r in records) + '\n{"partial":', encoding="utf-8")
            self.assertEqual(export_session(source, output), 2)
            messages = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(messages[0]["text"], "Please implement Arrangement MCP.")
            self.assertEqual(messages[1]["text"], "Visible result")


if __name__ == "__main__":
    unittest.main()
