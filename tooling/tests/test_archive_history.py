"""Tests for the isolated Git archive history."""

import json
import hashlib
import io
import errno
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import types
import unittest
import zlib
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agsdl import archive_history
from agsdl.archive_history import record_version, verify_history


@unittest.skipUnless(shutil.which("git"), "Git is not installed")
class ArchiveHistoryTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.snapshot = self.root / "snapshot"
        shutil.copytree(Path(__file__).resolve().parents[2] / "examples/review-project", self.snapshot)
        manifest = self.snapshot / "agsdl.json"
        project = json.loads(manifest.read_text(encoding="utf-8"))
        project["skills"] = {"history": {"uri": "skill/SKILL.md"}}
        manifest.write_text(json.dumps(project), encoding="utf-8")
        self.skill = self.snapshot / "skill"
        self.skill.mkdir()
        (self.skill / "SKILL.md").write_text("Instructions", encoding="utf-8")
        self.bundle = self.root / "history.bundle"
        (self.skill / "data").write_bytes(b"\x00one\r\n")

    def test_append_select_and_branch(self):
        first = record_version(self.snapshot, self.bundle, "first")
        (self.skill / "data").write_bytes(b"two")
        second = record_version(self.snapshot, self.bundle, "second")
        self.assertEqual(verify_history(self.bundle, self.snapshot), second)
        (self.skill / "data").write_bytes(b"\x00one\r\n")
        with self.assertRaisesRegex(ValueError, "tip"):
            verify_history(self.bundle, self.snapshot, first)
        (self.skill / "new").write_bytes(b"branch")
        original = self.bundle.read_bytes()
        with self.assertRaisesRegex(ValueError, "fork"):
            record_version(self.snapshot, self.bundle, "branch", parent=first)
        fork = self.root / "fork.bundle"
        branch = record_version(self.snapshot, self.bundle, "branch", parent=first, fork=fork)
        self.assertEqual(self.bundle.read_bytes(), original)
        self.assertEqual(verify_history(fork, self.snapshot), branch)
        with self.assertRaises(FileExistsError):
            record_version(self.snapshot, self.bundle, "branch", parent=first, fork=fork)
        with self.assertRaises(ValueError):
            verify_history(fork, self.snapshot, second)

    def test_content_paths_and_modes(self):
        path = self.skill / "data"
        path.chmod(0o755)
        nested = self.skill / "folder"
        nested.mkdir()
        filename = "-name with spaces"
        (nested / filename).write_bytes(b"binary\xff")
        commit = record_version(self.snapshot, self.bundle, "snapshot")
        self.assertEqual(verify_history(self.bundle, self.snapshot), commit)
        if os.name != "nt":
            path.chmod(0o644)
            with self.assertRaisesRegex(ValueError, "does not match"):
                verify_history(self.bundle, self.snapshot)
            path.chmod(0o755)
        path.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "does not match"):
            verify_history(self.bundle, self.snapshot)

    def test_invalid_inputs_and_failed_update_preserves_bundle(self):
        first = record_version(self.snapshot, self.bundle, "first")
        original = self.bundle.read_bytes()
        for parent in ("HEAD", "a" * 40, first[:8]):
            with self.subTest(parent=parent), self.assertRaises(ValueError):
                record_version(self.snapshot, self.bundle, "bad", parent)
            self.assertEqual(self.bundle.read_bytes(), original)
        with self.assertRaises(ValueError):
            record_version(self.snapshot, self.bundle, "")
        with self.assertRaises(ValueError):
            verify_history(self.bundle, self.snapshot, "HEAD")
        try:
            (self.skill / "link").symlink_to(self.skill / "data")
        except OSError:
            pass  # Creating symlinks may require privileges on Windows.
        else:
            with self.assertRaises(ValueError):
                record_version(self.snapshot, self.bundle, "link")
        self.assertEqual(self.bundle.read_bytes(), original)

    def test_lock_and_git_configuration_are_isolated(self):
        lock = self.bundle.with_name(self.bundle.name + ".lock")
        lock.touch()
        with self.assertRaises(FileExistsError):
            record_version(self.snapshot, self.bundle, "locked")
        lock.unlink()
        home = self.root / "home"
        home.mkdir()
        marker = self.root / "executed"
        (home / ".gitconfig").write_text('[core]\n\thooksPath = {}\n'.format(home))
        (home / "post-commit").write_text("#!/bin/sh\ntouch '{}'\n".format(marker))
        (home / "post-commit").chmod(0o755)
        with mock.patch.dict(os.environ, {"HOME": str(home), "GIT_DIR": str(home),
                                         "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "bad.key",
                                         "GIT_CONFIG_VALUE_0": "bad"}):
            commit = record_version(self.snapshot, self.bundle, "safe")
            self.assertEqual(verify_history(self.bundle, self.snapshot), commit)
        self.assertFalse(marker.exists())

    def test_history_rejects_a_different_project_id(self):
        record_version(self.snapshot, self.bundle, "first")
        original = self.bundle.read_bytes()
        manifest = self.snapshot / "agsdl.json"
        project = json.loads(manifest.read_text(encoding="utf-8"))
        project["id"] = "other-project"
        manifest.write_text(json.dumps(project), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "different project IDs"):
            record_version(self.snapshot, self.bundle, "second")
        self.assertEqual(self.bundle.read_bytes(), original)

    def test_older_revision_must_contain_only_selected_files(self):
        repo = self.root / "ordinary-history"
        shutil.copytree(self.snapshot, repo)
        def git(*args):
            return subprocess.run(["git", "-C", str(repo), "-c", "user.name=Test",
                                   "-c", "user.email=test@invalid", *args],
                                  check=True, capture_output=True)
        git("init")
        (repo / "notes.txt").write_text("A note", encoding="utf-8")
        git("add", ".")
        git("commit", "-m", "older")
        (repo / "notes.txt").unlink()
        git("add", "-u")
        git("commit", "-m", "current")
        git("branch", "versions")
        git("bundle", "create", "--version=2", str(self.bundle), "refs/heads/versions")
        with self.assertRaisesRegex(ValueError, "selected project files"):
            verify_history(self.bundle, self.snapshot)

    def test_empty_history_directory_is_rejected(self):
        record_version(self.snapshot, self.bundle, "first")
        with tempfile.TemporaryDirectory() as directory:
            repo = archive_history._Repository(directory)
            tip = repo.load(self.bundle)
            tree = repo.run("log", "--format=%T", tip).splitlines()[0]
            blobs, directories = repo.tree_entries(tree)
            directories.add("empty")
            with self.assertRaisesRegex(ValueError, "directory without selected files"):
                repo.validate_project_tree(blobs, directories, repo.directory / "blobs")

    def test_blob_materialization_without_hard_links(self):
        commit = record_version(self.snapshot, self.bundle, "first")
        with mock.patch.object(archive_history.os, "link", side_effect=OSError(errno.EPERM, "unsupported")):
            self.assertEqual(verify_history(self.bundle, self.snapshot), commit)

    def test_git_runs_in_private_directory(self):
        real_popen = subprocess.Popen
        with mock.patch.object(archive_history.subprocess, "Popen", wraps=real_popen) as popen:
            record_version(self.snapshot, self.bundle, "private")
        for call in popen.call_args_list:
            self.assertIn("agsdl-history-", str(call.kwargs["cwd"]))

    def test_rejects_invalid_or_incremental_bundle(self):
        self.bundle.write_bytes(b"not a bundle")
        with self.assertRaises(ValueError):
            verify_history(self.bundle, self.snapshot)
        self.bundle.unlink()
        first = record_version(self.snapshot, self.bundle, "first")
        (self.skill / "data").write_bytes(b"second")
        record_version(self.snapshot, self.bundle, "second")
        repo = self.root / "repo.git"
        subprocess.run(["git", "init", "--bare", str(repo)], check=True, capture_output=True)
        subprocess.run(["git", "--git-dir", str(repo), "fetch", str(self.bundle),
                        "refs/heads/versions:refs/heads/versions"], check=True, capture_output=True)
        incremental = self.root / "incremental.bundle"
        subprocess.run(["git", "--git-dir", str(repo), "bundle", "create", str(incremental),
                        "refs/heads/versions", "^" + first], check=True, capture_output=True)
        with self.assertRaises(ValueError):
            verify_history(incremental, self.snapshot)

    def test_bundle_format_and_resource_limits(self):
        record_version(self.snapshot, self.bundle, "first")
        original = self.bundle.read_bytes()
        for payload in (original.replace(b"# v2 git bundle", b"# v3 git bundle", 1),
                        original.replace(b"refs/heads/versions", b"refs/heads/other___", 1)):
            self.bundle.write_bytes(payload)
            with self.assertRaises(ValueError):
                verify_history(self.bundle, self.snapshot)
        self.bundle.write_bytes(original)
        for name, limit in (("_MAX_BUNDLE", len(original) - 1),
                            ("_MAX_OBJECTS", 1), ("_MAX_EXPANDED", 1),
                            ("_MAX_SECONDS", 0)):
            with self.subTest(limit=name), mock.patch.object(archive_history, name, limit):
                with self.assertRaises(ValueError):
                    verify_history(self.bundle, self.snapshot)
        directory = self.root / "not-a-file"
        directory.mkdir()
        with self.assertRaises(ValueError):
            verify_history(directory, self.snapshot)

    def test_preflight_counts_delta_result_sizes(self):
        base = b"A" * 20
        base_object = b"\xb4\x01" + zlib.compress(base)
        delta = bytes((20, 20, 0x90, 20))
        pack = (b"PACK\x00\x00\x00\x02\x00\x00\x00\x02" + base_object
                + b"\x64" + bytes((len(base_object),)) + zlib.compress(delta))
        pack += hashlib.sha1(pack).digest()
        source = io.BytesIO(pack)
        source.seek(12)
        archive_history._preflight_pack(source, 2, 0, time.monotonic() + 5)
        source.seek(12)
        with mock.patch.object(archive_history, "_MAX_EXPANDED", 30):
            with self.assertRaisesRegex(ValueError, "expansion limit"):
                archive_history._preflight_pack(source, 2, 0, time.monotonic() + 5)

    def test_new_bundle_is_validated_before_replacement(self):
        record_version(self.snapshot, self.bundle, "first")
        original = self.bundle.read_bytes()
        (self.skill / "new").write_bytes(os.urandom(2048))
        with mock.patch.object(archive_history, "_MAX_BUNDLE", len(original) + 100):
            with self.assertRaises(ValueError):
                record_version(self.snapshot, self.bundle, "too large")
        self.assertEqual(self.bundle.read_bytes(), original)
        self.assertFalse(self.bundle.with_name(self.bundle.name + ".lock").exists())

    def test_unreachable_objects_are_rejected(self):
        tip = record_version(self.snapshot, self.bundle, "first")
        repo = self.root / "build.git"
        subprocess.run(["git", "init", "--bare", str(repo)], check=True, capture_output=True)
        git = ["git", "--git-dir", str(repo)]
        subprocess.run(git + ["bundle", "unbundle", str(self.bundle)], check=True, capture_output=True)
        extra = subprocess.run(git + ["hash-object", "-w", "--stdin"], input=b"extra",
                               check=True, capture_output=True).stdout.strip()
        packed = subprocess.run(git + ["pack-objects", "--stdout", "--revs"],
                                input=tip.encode() + b"\n" + extra + b"\n",
                                check=True, capture_output=True).stdout
        self.bundle.write_bytes(b"# v2 git bundle\n" + tip.encode() +
                                b" refs/heads/versions\n\n" + packed)
        with self.assertRaisesRegex(ValueError, "unreachable"):
            verify_history(self.bundle, self.snapshot)

    @unittest.skipIf(os.name == "nt", "Windows does not preserve executable mode bits")
    def test_explicit_executable_set_and_tip_requirement(self):
        (self.skill / "data").chmod(0o755)
        first = record_version(self.snapshot, self.bundle, "first")
        (self.skill / "data").chmod(0o644)
        self.assertEqual(verify_history(self.bundle, self.snapshot, first,
                                        executables={"skill/data"}), first)
        (self.skill / "data").write_bytes(b"second")
        record_version(self.snapshot, self.bundle, "second")
        with self.assertRaisesRegex(ValueError, "tip"):
            verify_history(self.bundle, self.snapshot, first, executables={"skill/data"})

    def test_record_explicit_executable_set(self):
        commit = record_version(self.snapshot, self.bundle, "mode", executables={"skill/data"})
        self.assertEqual(verify_history(self.bundle, self.snapshot, commit, executables={"skill/data"}), commit)
        with self.assertRaisesRegex(ValueError, "does not match"):
            verify_history(self.bundle, self.snapshot, commit, executables=set())

    def test_hashing_batches_paths_with_spaces_without_filters(self):
        (self.skill / ".gitattributes").write_text("* text eol=lf\n")
        for index in range(260):
            (self.skill / ("file {:03d} with spaces".format(index))).write_bytes(b"a\r\nb")
        real_popen = subprocess.Popen
        with mock.patch.object(archive_history.subprocess, "Popen", wraps=real_popen) as popen:
            commit = record_version(self.snapshot, self.bundle, "batch")
        commands = [call.args[0] for call in popen.call_args_list]
        hashes = [command for command in commands if "hash-object" in command]
        self.assertEqual(len(hashes), 3)
        self.assertTrue(all("--no-filters" in command for command in hashes))
        self.assertEqual(verify_history(self.bundle, self.snapshot), commit)

    def test_unavailable_resource_limits_and_output_cap(self):
        record_version(self.snapshot, self.bundle, "first")
        windows_os = types.SimpleNamespace(**vars(os))
        windows_os.name = "nt"
        real_popen = subprocess.Popen
        with mock.patch.object(archive_history, "os", windows_os), \
             mock.patch.dict(os.environ, {"PATH": str(self.root) + os.pathsep + os.environ.get("PATH", "")}), \
             mock.patch.object(archive_history.subprocess, "Popen", wraps=real_popen) as popen:
            verify_history(self.bundle, self.snapshot)
        self.assertTrue(all(Path(call.args[0][0]).is_absolute() and
                            Path(call.args[0][0]).stem.lower() == "git"
                            for call in popen.call_args_list))
        with mock.patch.object(archive_history, "_MAX_STREAM", 1):
            with self.assertRaisesRegex(ValueError, "output exceeds"):
                verify_history(self.bundle, self.snapshot)


if __name__ == "__main__":
    unittest.main()
