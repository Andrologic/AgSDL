"""End-to-end tests for portable project archives and offline history."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile

TOOLING = Path(__file__).resolve().parents[1]
EXAMPLE = TOOLING.parent / "examples/review-project"


class ArchiveTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.project = shutil.copytree(EXAMPLE, self.base / "project")
        self.archive = self.base / "project.agsdl"

    def cli(self, *args, ok=True, env=None):
        result = subprocess.run(
            [sys.executable, "-m", "agsdl.archive", *(str(arg) for arg in args)],
            cwd=TOOLING, env=env, text=True, capture_output=True,
        )
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def pack(self, *args):
        self.cli("pack", self.project, self.archive, *args)

    def entries(self):
        with zipfile.ZipFile(self.archive) as archive:
            return {info.filename: archive.read(info) for info in archive.infolist()}

    def rewrite(self, change):
        with zipfile.ZipFile(self.archive) as archive:
            entries = [(info, archive.read(info)) for info in archive.infolist()]
        entries = change(entries)
        with zipfile.ZipFile(self.archive, "w") as archive:
            for info, data in entries:
                archive.writestr(info, data)

    def reject(self):
        destination = self.base / "rejected"
        self.cli("inspect", self.archive, ok=False)
        self.cli("unpack", self.archive, destination, ok=False)
        self.assertFalse(destination.exists())

    def test_reproducible_relocated_snapshot_and_inventory(self):
        self.pack()
        original = self.archive.read_bytes()
        second = self.base / "second.agsdl"
        self.cli("pack", self.project, second)
        self.assertEqual(second.read_bytes(), original)
        entries = self.entries()
        inventory = json.loads(entries["archive.json"])
        self.assertEqual(inventory["archiveFormat"], "agsdl-archive-1")
        self.assertNotIn("history", inventory)
        self.assertEqual(set(entries), {"archive.json"} | {
            "project/" + path for path in inventory["files"]})
        for path, metadata in inventory["files"].items():
            data = entries["project/" + path]
            self.assertEqual(metadata, {
                "size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                "executable": bool((self.project / path).stat().st_mode & 0o111),
            })
        report = json.loads(self.cli("inspect", self.archive).stdout)
        self.assertEqual(report["requiredSecrets"], {"issues": ["ISSUES_TOKEN"]})
        self.assertEqual(report["inventory"], inventory)
        for module, expected in (("agsdl", "valid (0 errors"), ("agsdl.mermaid", "flowchart")):
            check = subprocess.run([sys.executable, "-m", module, str(self.archive)],
                                   cwd=TOOLING, text=True, capture_output=True, check=True)
            self.assertIn(expected, check.stdout)
        target = self.base / "relocated"
        self.cli("unpack", self.archive, target)
        for path in inventory["files"]:
            self.assertEqual((target / path).read_bytes(), (self.project / path).read_bytes())
        self.cli("unpack", self.archive, target, ok=False)
        self.assertEqual((target / "agsdl.json").read_bytes(), (self.project / "agsdl.json").read_bytes())

    def test_only_declared_files_and_complete_skill_directory(self):
        manifest_path = self.project / "agsdl.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["skills"] = {"review": {"uri": "skills/review/SKILL.md"}}
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        skill = self.project / "skills/review"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("Review.", encoding="utf-8")
        (skill / "helper.txt").write_text("Included", encoding="utf-8")
        for name in ("notes.txt", "agents/reviewer/extra.txt", ".env", ".git/config",
                     ".agsdl-history.bundle", "skills/other/SKILL.md"):
            path = self.project / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Excluded", encoding="utf-8")
        self.pack()
        files = set(json.loads(self.entries()["archive.json"])["files"])
        self.assertIn("skills/review/SKILL.md", files)
        self.assertIn("skills/review/helper.txt", files)
        for name in ("notes.txt", "agents/reviewer/extra.txt", ".env", ".git/config",
                     ".agsdl-history.bundle", "skills/other/SKILL.md"):
            self.assertNotIn(name, files)

    def test_corrupt_inventory_and_unexpected_members_are_rejected(self):
        def alter_inventory(field, value):
            def change(entries):
                result = []
                for info, data in entries:
                    if info.filename == "archive.json":
                        manifest = json.loads(data)
                        first = next(iter(manifest["files"]))
                        manifest["files"][first][field] = value
                        data = json.dumps(manifest).encode()
                    result.append((info, data))
                return result
            return change

        for field, value in (("size", 999999), ("sha256", "0" * 64), ("executable", "yes")):
            with self.subTest(field=field):
                self.archive.unlink(missing_ok=True)
                self.pack()
                self.rewrite(alter_inventory(field, value))
                self.reject()
        for name in ("extra", "project/unexpected", "project/../escape", "/absolute",
                     "project/evil\\name"):
            with self.subTest(name=name):
                self.archive.unlink(missing_ok=True)
                self.pack()
                self.rewrite(lambda entries: entries + [(name, b"unexpected")])
                self.reject()
        self.archive.unlink(missing_ok=True)
        self.pack()
        with self.assertWarns(UserWarning):
            self.rewrite(lambda entries: entries + [("archive.json", b"{}")])
        self.reject()
        for name in ("../escape", "/absolute", "evil\\name"):
            with self.subTest(inventory_path=name):
                self.archive.unlink(missing_ok=True)
                self.pack()
                def unsafe_path(entries):
                    changed = []
                    for info, data in entries:
                        if info.filename == "archive.json":
                            manifest = json.loads(data)
                            manifest["files"][name] = {
                                "size": 1, "sha256": hashlib.sha256(b"x").hexdigest(),
                                "executable": False,
                            }
                            data = json.dumps(manifest).encode()
                        changed.append((info, data))
                    return changed + [("project/" + name, b"x")]
                self.rewrite(unsafe_path)
                self.reject()

    def test_symlink_member_is_rejected(self):
        self.pack()
        def change(entries):
            result = []
            for info, data in entries:
                if info.filename.startswith("project/"):
                    info.create_system = 3
                    info.external_attr = (stat.S_IFLNK | 0o777) << 16
                    result.append((info, data))
                    return result + entries[len(result):]
                result.append((info, data))
            self.fail("archive has no project file")
        self.rewrite(change)
        self.reject()

    @unittest.skipUnless(shutil.which("git"), "Git is required for history")
    def test_offline_history_and_branch(self):
        store = self.base / "versions.bundle"
        content = self.project / "agents/reviewer/instructions.md"
        commits = []
        for number in range(1, 4):
            content.write_text(f"Version {number}\n", encoding="utf-8")
            self.cli("version", self.project, store, "-m", f"Version {number}")
            heads = subprocess.run(["git", "bundle", "list-heads", str(store)],
                                   capture_output=True, text=True, check=True).stdout
            commits.append(heads.split()[0])
        self.pack("--history", store)
        entries = self.entries()
        history = json.loads(entries["archive.json"])["history"]
        self.assertEqual(history, {"commit": commits[2], "size": len(entries["history.bundle"]),
                                   "sha256": hashlib.sha256(entries["history.bundle"]).hexdigest()})
        target = self.base / "restored"
        self.cli("unpack", self.archive, target, "--with-history")
        restored = target / ".agsdl-history.bundle"
        self.assertEqual(restored.read_bytes(), entries["history.bundle"])
        clone = self.base / "clone"
        subprocess.run(["git", "clone", "-b", "versions", str(restored), str(clone)],
                       capture_output=True, check=True)
        log = subprocess.run(["git", "-C", str(clone), "log", "--format=%s"],
                             capture_output=True, text=True, check=True).stdout.splitlines()
        self.assertEqual(log, ["Version 3", "Version 2", "Version 1"])
        shown = subprocess.run(["git", "-C", str(clone), "show",
                                commits[0] + ":agents/reviewer/instructions.md"],
                               capture_output=True, text=True, check=True).stdout
        self.assertEqual(shown, "Version 1\n")
        subprocess.run(["git", "-C", str(clone), "checkout", "--detach", commits[1]],
                       capture_output=True, check=True)
        self.assertEqual((clone / "agents/reviewer/instructions.md").read_text(), "Version 2\n")
        branch = self.base / "branch.bundle"
        content.write_text("Alternative\n", encoding="utf-8")
        self.cli("version", self.project, restored, "-m", "Alternative", "--parent", commits[0],
                 "--fork", branch)
        self.assertEqual(restored.read_bytes(), entries["history.bundle"])
        branch_clone = self.base / "branch-clone"
        subprocess.run(["git", "clone", "-b", "versions", str(branch), str(branch_clone)],
                       capture_output=True, check=True)
        log = subprocess.run(["git", "-C", str(branch_clone), "log", "--format=%s"],
                             capture_output=True, text=True, check=True).stdout.splitlines()
        self.assertEqual(log, ["Alternative", "Version 1"])
        self.assertEqual((branch_clone / "agents/reviewer/instructions.md").read_text(), "Alternative\n")

        # Snapshot operations do not need Git, even when an archive carries history.
        no_git = dict(os.environ, PATH=str(self.base / "empty-path"))
        self.cli("inspect", self.archive, env=no_git)
        snapshot = self.base / "snapshot-only"
        self.cli("unpack", self.archive, snapshot, env=no_git)
        self.assertFalse((snapshot / ".agsdl-history.bundle").exists())
        self.assertEqual((snapshot / "agents/reviewer/instructions.md").read_text(), "Version 3\n")
        other = self.base / "without-git.agsdl"
        self.cli("pack", snapshot, other, env=no_git)


if __name__ == "__main__":
    unittest.main()
