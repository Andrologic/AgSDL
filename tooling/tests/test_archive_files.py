"""Project archive dependency discovery."""

import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

TOOLING = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLING))
from agsdl.archive_files import check_portable_name, open_portable_file, portable_files
from agsdl.project import load_project
from agsdl.validator import validate_document

EXAMPLE = TOOLING.parent / "examples/review-project"


class ArchiveFilesTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = shutil.copytree(EXAMPLE, Path(temp.name) / "project")
        self.entry = self.root / "agsdl.json"
        self.manifest = json.loads(self.entry.read_text())

    def save(self):
        self.entry.write_text(json.dumps(self.manifest), encoding="utf-8")

    def skill(self):
        self.manifest["skills"] = {"review": {"uri": "skill/SKILL.md"}}
        directory = self.root / "skill"
        directory.mkdir()
        (directory / "SKILL.md").write_text("instructions")
        return directory

    def test_declared_files_and_complete_skill(self):
        directory = self.skill()
        (directory / "scripts").mkdir()
        (directory / "scripts/run.py").write_text("pass")
        (self.root / "orphan.txt").write_text("ignored")
        (self.root / "mcp/asset.js").write_text("asset")
        self.manifest["mcpServers"]["issues"] = {"command": ["node"]}
        self.manifest["mcpFiles"] = {"issues": ["mcp/asset.js"]}
        self.manifest["content"] = {"remote": {"uri": "https://example.org/file"}}
        self.save()
        files = portable_files(self.root)
        expected = {"agsdl.json", "agents/reviewer/agent.json", "agents/reviewer/instructions.md",
                    "flows/review.json", "harnesses/codex/reviewer.json", "secrets/requirements.json",
                    "mcp/asset.js", "skill/SKILL.md", "skill/scripts/run.py"}
        self.assertEqual(set(files), expected)
        for name, path in files.items():
            self.assertEqual(path, self.root / name)
            self.assertEqual(path.read_bytes(), (self.root / name).read_bytes())

    def test_validation_uses_supplied_modules(self):
        modules = {}
        with mock.patch("agsdl.archive_files.validate_document", wraps=validate_document) as validate:
            portable_files(self.root, modules=modules)
        self.assertIs(validate.call_args.args[1], modules)

    def test_portable_names(self):
        for name in ("", "/a", "a//b", "a/../b", "a/./b", "a\\b", "C:foo", "nul.txt",
                     "COM¹.txt", "a/aux", "name.", "name ", "x\x7f", ".GIT/config",
                     "a/.env", "a/.ENV.local", "a/.AgSDL-history.bundle"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                check_portable_name(name)
        for name in ("a/b.txt", ".env-example", "normal/é.txt"):
            check_portable_name(name)

    def test_skill_tree_rejects_private_special_and_colliding_entries(self):
        directory = self.skill()
        self.save()
        for name in (".env.local", ".git", ".agsdl-history.bundle", "CON.txt"):
            path = directory / name
            path.write_text("private")
            with self.subTest(name=name), self.assertRaises(ValueError):
                portable_files(self.root)
            path.unlink()
        (directory / "É").mkdir()
        (directory / "e\u0301").mkdir()
        with self.assertRaisesRegex(ValueError, "collision"):
            portable_files(self.root)
        (directory / "e\u0301").rmdir()
        (directory / "É").rmdir()
        if hasattr(os, "mkfifo"):
            os.mkfifo(directory / "pipe")
            with self.assertRaises(ValueError):
                portable_files(self.root)

    def test_symlinks_rejected_but_normal_loader_unchanged(self):
        original = self.root / "agents/reviewer/instructions.md"
        link = self.root / "agents/reviewer/link.md"
        link.symlink_to(original.name)
        agent = self.root / "agents/reviewer/agent.json"
        data = json.loads(agent.read_text())
        data["instructions"][0]["uri"] = "link.md"
        agent.write_text(json.dumps(data))
        load_project(self.root)
        with self.assertRaisesRegex(ValueError, "symbolic link"):
            portable_files(self.root)

    def test_skill_tree_rejects_symlink_and_parent_case_collision(self):
        directory = self.skill()
        (directory / "extra").symlink_to("SKILL.md")
        self.save()
        with self.assertRaisesRegex(ValueError, "symbolic link"):
            portable_files(self.root)
        (directory / "extra").unlink()
        (directory / "Scripts").mkdir()
        (directory / "scripts").mkdir()
        with self.assertRaisesRegex(ValueError, "collision"):
            portable_files(self.root)

    def test_declared_private_file_is_rejected(self):
        (self.root / ".env").write_text("secret")
        self.manifest["content"] = {"private": {"uri": ".env"}}
        self.save()
        load_project(self.root)
        with self.assertRaises(ValueError):
            portable_files(self.root)

    def test_open_portable_file_checks_parents_and_regular_mode(self):
        with open_portable_file(self.root, "agents/reviewer/instructions.md") as handle:
            self.assertTrue(handle.read())
            self.assertTrue(os.fstat(handle.fileno()).st_mode)
        (self.root / "linked").symlink_to("agents", target_is_directory=True)
        (self.root / "link.md").symlink_to("agents/reviewer/instructions.md")
        for name in ("linked/reviewer/instructions.md", "link.md", "agents", "../outside"):
            with self.subTest(name=name), self.assertRaises((ValueError, OSError)):
                with open_portable_file(self.root, name):
                    pass
        if hasattr(os, "mkfifo"):
            os.mkfifo(self.root / "pipe")
            with self.assertRaises((ValueError, OSError)):
                with open_portable_file(self.root, "pipe"):
                    pass

    def test_discovery_limits_and_overlapping_skills(self):
        directory = self.skill()
        (directory / "nested").mkdir()
        (directory / "nested/SKILL.md").write_text("nested")
        self.manifest["skills"]["nested"] = {"uri": "skill/nested/SKILL.md"}
        self.save()
        with mock.patch("agsdl.archive_files.os.scandir", wraps=os.scandir) as scandir:
            files = portable_files(self.root)
        self.assertEqual(sum(Path(call.args[0]) == directory / "nested"
                             for call in scandir.call_args_list), 1)
        self.assertIn("skill/nested/SKILL.md", files)
        with mock.patch("agsdl.archive_files.MAX_FILES", len(files) - 1):
            with self.assertRaisesRegex(ValueError, "too many project files"):
                portable_files(self.root)
        with mock.patch("agsdl.archive_files.MAX_PATHS", 1):
            with self.assertRaisesRegex(ValueError, "too many project paths"):
                portable_files(self.root)

    def test_declaration_json_limits_do_not_change_normal_loader(self):
        settings = self.root / "harnesses/codex/reviewer.json"
        for value, message in (({"x": "a" * 256}, "size"),
                               ({"x": [0] * 1025}, "array"),
                               ({"x": {"y": 1}}, "nesting")):
            if message == "nesting":
                value = 0
                for _ in range(65):
                    value = {"x": value}
            settings.write_text(json.dumps(value))
            load_project(self.root)
            if message == "size":
                with mock.patch("agsdl.archive_files.MAX_JSON", 128):
                    with self.assertRaisesRegex(ValueError, "size"):
                        portable_files(self.root)
            else:
                with self.assertRaisesRegex(ValueError, message):
                    portable_files(self.root)

    def test_declaration_aggregate_limit_does_not_limit_assets(self):
        directory = self.skill()
        (directory / "large.txt").write_bytes(b"x" * 2048)
        self.save()
        with mock.patch("agsdl.archive_files.MAX_JSON_TOTAL", 1):
            with self.assertRaisesRegex(ValueError, "size"):
                portable_files(self.root)
        with mock.patch("agsdl.archive_files.MAX_JSON", 1024):
            self.assertIn("skill/large.txt", portable_files(self.root))

    def test_rejects_root_skill_and_invalid_semantics(self):
        (self.root / "SKILL.md").write_text("skill")
        self.manifest["skills"] = {"root": {"uri": "SKILL.md"}}
        self.save()
        with self.assertRaisesRegex(ValueError, "project root"):
            portable_files(self.root)
        self.manifest.pop("skills")
        self.manifest["agents"]["missing"] = {"file": "agents/reviewer/agent.json"}
        self.manifest["flow"] = {"entry": "start", "steps": {
            "start": {"type": "agent", "agent": "absent"}}}
        self.save()
        with self.assertRaises(ValueError):
            portable_files(self.root)


if __name__ == "__main__":
    unittest.main()
