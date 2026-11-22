"""Tests for the isolated Git archive history."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
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
        self.snapshot.mkdir()
        self.bundle = self.root / "history.bundle"
        (self.snapshot / "data").write_bytes(b"\x00one\r\n")

    def test_append_select_and_branch(self):
        first = record_version(self.snapshot, self.bundle, "first")
        (self.snapshot / "data").write_bytes(b"two")
        second = record_version(self.snapshot, self.bundle, "second")
        self.assertEqual(verify_history(self.bundle, self.snapshot), second)
        (self.snapshot / "data").write_bytes(b"\x00one\r\n")
        with self.assertRaisesRegex(ValueError, "tip"):
            verify_history(self.bundle, self.snapshot, first)
        (self.snapshot / "new").write_bytes(b"branch")
        branch = record_version(self.snapshot, self.bundle, "branch", parent=first)
        self.assertEqual(verify_history(self.bundle, self.snapshot), branch)
        with self.assertRaises(ValueError):
            verify_history(self.bundle, self.snapshot, second)

    def test_content_paths_and_modes(self):
        path = self.snapshot / "data"
        path.chmod(0o755)
        nested = self.snapshot / "folder"
        nested.mkdir()
        filename = "-name with spaces" if os.name == "nt" else "-name\tline\n"
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
            (self.snapshot / "link").symlink_to(self.snapshot / "data")
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

    def test_rejects_invalid_or_incremental_bundle(self):
        self.bundle.write_bytes(b"not a bundle")
        with self.assertRaises(ValueError):
            verify_history(self.bundle, self.snapshot)
        self.bundle.unlink()
        first = record_version(self.snapshot, self.bundle, "first")
        (self.snapshot / "data").write_bytes(b"second")
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

    def test_new_bundle_is_validated_before_replacement(self):
        record_version(self.snapshot, self.bundle, "first")
        original = self.bundle.read_bytes()
        (self.snapshot / "new").write_bytes(os.urandom(2048))
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
        (self.snapshot / "data").chmod(0o755)
        first = record_version(self.snapshot, self.bundle, "first")
        (self.snapshot / "data").chmod(0o644)
        self.assertEqual(verify_history(self.bundle, self.snapshot, first,
                                        executables={"data"}), first)
        (self.snapshot / "data").write_bytes(b"second")
        record_version(self.snapshot, self.bundle, "second")
        with self.assertRaisesRegex(ValueError, "tip"):
            verify_history(self.bundle, self.snapshot, first, executables={"data"})

    def test_hashing_batches_paths_with_spaces_without_filters(self):
        (self.snapshot / ".gitattributes").write_text("* text eol=lf\n")
        for index in range(260):
            (self.snapshot / ("file {:03d} with spaces".format(index))).write_bytes(b"a\r\nb")
        real_popen = subprocess.Popen
        with mock.patch.object(archive_history.subprocess, "Popen", wraps=real_popen) as popen:
            commit = record_version(self.snapshot, self.bundle, "batch")
        commands = [call.args[0] for call in popen.call_args_list]
        hashes = [command for command in commands if "hash-object" in command]
        self.assertEqual(len(hashes), 3)
        self.assertTrue(all("--no-filters" in command for command in hashes))
        self.assertEqual(verify_history(self.bundle, self.snapshot), commit)

    def test_windows_command_path_and_output_cap(self):
        record_version(self.snapshot, self.bundle, "first")
        windows_os = types.SimpleNamespace(**vars(os))
        windows_os.name = "nt"
        real_popen = subprocess.Popen
        with mock.patch.object(archive_history, "os", windows_os), \
             mock.patch.object(archive_history.subprocess, "Popen", wraps=real_popen) as popen:
            verify_history(self.bundle, self.snapshot)
        self.assertTrue(all(call.args[0][0] == "git" for call in popen.call_args_list))
        self.assertTrue(all(not call.kwargs["start_new_session"] for call in popen.call_args_list))
        with mock.patch.object(archive_history, "_MAX_STREAM", 1):
            with self.assertRaisesRegex(ValueError, "output exceeds"):
                verify_history(self.bundle, self.snapshot)


if __name__ == "__main__":
    unittest.main()
