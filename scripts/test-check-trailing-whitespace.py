#!/usr/bin/env python3
"""Fault tests for the dependency-free trailing-whitespace check."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name('check-trailing-whitespace.py')


def run(root):
    return subprocess.run([sys.executable, str(SCRIPT), str(root)], capture_output=True, text=True)


class TrailingWhitespaceTests(unittest.TestCase):
    def test_clean_tree_passes(self):
        with tempfile.TemporaryDirectory() as root:
            Path(root, 'a.md').write_text('clean\r\nline\n')
            self.assertEqual(run(root).returncode, 0)

    def test_blank_at_line_end_fails_with_location(self):
        with tempfile.TemporaryDirectory() as root:
            Path(root, 'docs').mkdir()
            Path(root, 'docs', 'a.yaml').write_text('ok\nbad\t\n')
            result = run(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn('docs/a.yaml:2: trailing whitespace', result.stdout)

    def test_other_suffixes_and_skipped_directories_are_ignored(self):
        with tempfile.TemporaryDirectory() as root:
            Path(root, 'a.txt').write_text('bad \n')
            Path(root, '.git').mkdir()
            Path(root, '.git', 'b.md').write_text('bad \n')
            self.assertEqual(run(root).returncode, 0)


if __name__ == '__main__':
    unittest.main()
