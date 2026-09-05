#!/usr/bin/env python3
"""Focused tests for the local Markdown link checker."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


CHECKER = Path(__file__).with_name("check-markdown-links.py")


class MarkdownLinkCheckerTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def write(self, relative_path, content=""):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def run_checker(self, *paths):
        targets = paths or (self.root,)
        return subprocess.run(
            [sys.executable, str(CHECKER), *(str(path) for path in targets)],
            capture_output=True,
            check=False,
            text=True,
        )

    def test_accepts_existing_file(self):
        self.write("README.md", "[guide](docs/guide.md)\n")
        self.write("docs/guide.md", "# Guide\n")

        result = self.run_checker()

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_reports_missing_file(self):
        self.write("README.md", "[missing](docs/missing.md)\n")

        result = self.run_checker()

        self.assertEqual(result.returncode, 1)
        self.assertIn("README.md:1", result.stderr)
        self.assertIn("docs/missing.md", result.stderr)

    def test_rejects_missing_input_path(self):
        missing_input = self.root / "missing-input"

        result = self.run_checker(missing_input)

        self.assertEqual(result.returncode, 2)
        self.assertIn("Markdown check path does not exist", result.stderr)
        self.assertIn(str(missing_input), result.stderr)

    def test_resolves_from_the_source_file(self):
        self.write("README.md", "# Project\n")
        self.write("docs/reference.md", "# Reference\n")
        self.write(
            "docs/nested/guide.md",
            "[root](../../README.md#project)\n[peer](../reference.md?view=full)\n",
        )

        result = self.run_checker()

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_ignores_urls_anchors_and_fenced_code(self):
        self.write(
            "README.md",
            "[web](https://example.invalid/missing.md)\n"
            "[mail](mailto:docs@example.invalid)\n"
            "[site path](/missing.md)\n"
            "[anchor](#missing)\n"
            "`[inline code](missing-inline.md)`\n"
            "`literal ``` [code](missing-with-longer-delimiter.md)`\n"
            "```md\n[code](missing-in-code.md)\n```\n"
            "~~~\n[more code](also-missing.md)\n~~~\n",
        )

        result = self.run_checker()

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_ignores_destination_with_parentheses(self):
        self.write("README.md", "[nested](existing(thing).md)\n")
        self.write("existing(thing).md")

        result = self.run_checker()

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_supports_angle_paths_percent_encoding_and_images(self):
        self.write(
            "README.md",
            "[spaced](<notes with spaces.md#part>)\n"
            "[encoded](encoded%20notes.md)\n"
            "![image](images/example.png)\n",
        )
        self.write("notes with spaces.md")
        self.write("encoded notes.md")
        self.write("images/example.png")

        result = self.run_checker()

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
